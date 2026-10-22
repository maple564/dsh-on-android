#!/bin/sh
# install.sh — 在 musl/aarch64 Linux (Alpine, PRoot 容器) 里安装 DeepSeek Harness
# 用法: sh install.sh [安装目录，默认 /opt/dsh-harness]
set -eu

DSH_HOME="${1:-/opt/dsh-harness}"
BIN_DIR="/usr/local/bin"

log() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# ---------- 0. 环境检查 ----------
command -v node >/dev/null 2>&1 || die "找不到 node，先 apk add nodejs npm"
command -v npm  >/dev/null 2>&1 || die "找不到 npm，先 apk add nodejs npm"
NODE_MAJOR=$(node -v | sed 's/^v\([0-9]*\).*/\1/')
[ "$NODE_MAJOR" -ge 20 ] || die "需要 Node >= 20（当前 $(node -v)）"
log "node $(node -v) / npm $(npm -v)"

# ---------- 1. 编译工具链（node-pty 需要） ----------
if ! command -v g++ >/dev/null 2>&1; then
  log "安装编译工具链 build-base linux-headers python3"
  apk add --no-cache build-base linux-headers python3
fi

# ---------- 2. 拉取 dsh ----------
log "安装 @deepseek-ai/dsh（首次约 400-600MB，耐心等）"
WORK=$(mktemp -d)
cd "$WORK"
npm install --no-audit --no-fund @deepseek-ai/dsh@latest
[ -f "$WORK/node_modules/@deepseek-ai/dsh/lib/bin.js" ] || die "安装后找不到 lib/bin.js"

# ---------- 3. 针对 musl 重编译 node-pty ----------
PTY_DIR="$WORK/node_modules/node-pty"
if [ -d "$PTY_DIR" ]; then
  log "重编译 node-pty（musl）"
  ( cd "$PTY_DIR" && npx --yes node-gyp rebuild )
  ( cd "$PTY_DIR" && node -e "const pty=require('./lib/index.js');const p=pty.spawn('/bin/echo',['ok'],{});p.onExit(e=>{console.log('node-pty OK',e.exitCode);process.exit(0)})" ) \
    || die "node-pty 编译后自检失败"
else
  log "未发现 node-pty（新版本可能已移除），跳过"
fi

# ---------- 4. 固化到稳定路径（PRoot 下 cp -a 会失败，用 tar 流） ----------
log "固化到 $DSH_HOME"
rm -rf "$DSH_HOME"
mkdir -p "$DSH_HOME"
( cd "$WORK/node_modules" && tar cf - . ) | ( cd "$DSH_HOME" && tar xf - )
mkdir -p "$DSH_HOME/node_modules"
for f in "$DSH_HOME"/* ; do
  case "$(basename "$f")" in
    node_modules) ;;
    *) mv "$f" "$DSH_HOME/node_modules/";;
  esac
done

# ---------- 5. wrapper ----------
log "写入 $BIN_DIR/dsh 与 $BIN_DIR/dsh-go"
cat > "$BIN_DIR/dsh" <<EOF
#!/bin/sh
# dsh wrapper — 固化版 $DSH_HOME
# --expose-internals: HMR 插件要求，且不能放在 NODE_OPTIONS 里
# DSH_PERMISSION_MODE: bootstrap 变量，只能由启动进程 export
export DSH_PERMISSION_MODE="\${DSH_PERMISSION_MODE:-danger-full-access}"
exec node --expose-internals $DSH_HOME/node_modules/@deepseek-ai/dsh/lib/bin.js "\$@"
EOF
chmod +x "$BIN_DIR/dsh"

cat > "$BIN_DIR/dsh-go" <<'EOF'
#!/bin/sh
# dsh-go — 启动 dsh web 并打开浏览器
URL="${DSH_URL:-http://127.0.0.1:3080}"
LOG="${DSH_LOG:-$HOME/.dsh-web.log}"

alive() { curl -s --max-time 3 -o /dev/null "$URL/" 2>/dev/null; }

case "${1:-}" in
  --status) alive && echo "运行中: $URL" || echo "未运行"; exit 0;;
esac

if ! alive; then
  echo "启动中..."
  nohup dsh web > "$LOG" 2>&1 &
  i=0
  while [ $i -lt 60 ]; do
    alive && break
    i=$((i+2)); sleep 2
  done
  alive || { echo "启动失败，看日志: $LOG"; tail -20 "$LOG"; exit 1; }
fi

case "${1:-}" in
  --browser) command -v android-open >/dev/null 2>&1 && android-open "$URL" || echo "打开 $URL";;
  *)         command -v minis-open   >/dev/null 2>&1 && minis-open   "$URL" || echo "打开 $URL";;
esac
EOF
chmod +x "$BIN_DIR/dsh-go"

log "完成。验证： dsh --version"
echo
echo "下一步："
echo "  export DEEPSEEK_API_KEY=sk-xxxxxxxx    # 也可以写进 ~/.dsh/.env（只放这一行）"
echo "  dsh-go"
