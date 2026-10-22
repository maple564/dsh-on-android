# 排错手册

按「你看到什么」查，不按「可能是什么原因」查。每条都给：报错原文 → 真正原因 → 命令。

先跑一遍体检，把输出贴进 issue：

```bash
echo "== uname =="; uname -a
echo "== libc =="; ldd --version 2>&1 | head -1   # musl 会报 "musl libc"
echo "== node =="; node -v; npm -v
echo "== dsh =="; dsh --version
echo "== 固化目录 =="; ls -d /opt/dsh-harness/node_modules/@deepseek-ai/dsh/lib/bin.js
echo "== node-pty =="; ls /opt/dsh-harness/node_modules/node-pty/build/Release/ 2>/dev/null
echo "== 服务 =="; curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3080/
```

---

## 安装阶段

### `Error loading shared library ld-linux-aarch64.so.1: No such file or directory`

**原因**：node-pty 用了 npm 上的 glibc 预编译二进制，musl 环境没有 glibc 的动态加载器。

**解决**：
```bash
apk add --no-cache build-base linux-headers python3
cd /opt/dsh-harness/node_modules/node-pty && npx --yes node-gyp rebuild
```
看到 `gyp info ok` 才算成功。编译需要 3-10 分钟（手机 CPU 慢）。

### `Cannot find module '/opt/dsh-harness/node_modules/...'`

**原因**：tar 流复制后目录层级被铺平了，`require` 从 `/opt/dsh-harness/<pkg>` 找不到（应该在 `node_modules/<pkg>`）。

**解决**：
```bash
cd /opt/dsh-harness && mkdir -p node_modules
for f in *; do [ "$f" = node_modules ] && continue; mv "$f" node_modules/; done
[ -d .bin ] && mv .bin node_modules/ 2>/dev/null
```

### `npm error ENOTEMPTY ... rename` / `cp: cannot create hard link`

**原因**：PRoot 下的文件系统视图不支持硬链接，`npm` / `cp -a` 都会踩。

**解决**：全局换成 tar 流：
```bash
tar cf - --exclude='node-pty/build' . | (cd "$TARGET" && tar xf -)
```

### `gyp ERR! stack Error: not found: make`

**解决**：`apk add --no-cache make g++`（`build-base` 已包含，但精简镜像可能被拆开装）。

---

## 启动阶段

### `--expose-internals is required for HMR` / `--expose-internals is not allowed in NODE_OPTIONS`

**原因**：HMR 插件需要该参数；但 Node 出于安全不允许它通过 `NODE_OPTIONS` 传入。

**解决**：写进 wrapper，直接传给 node：
```sh
exec node --expose-internals /opt/dsh-harness/node_modules/@deepseek-ai/dsh/lib/bin.js "$@"
```

### `.env sets DSH_PERMISSION_MODE, but only the launching environment may set it`

**原因**：`DSH_PERMISSION_MODE` 属于 bootstrap 变量，只认启动进程的环境。写进 `~/.dsh/.env` 会被显式拒绝 —— 这是防止「用配置文件偷偷提权」的设计。

**解决**：从 `.env` 删除，改在 wrapper 里 `export`：
```sh
export DSH_PERMISSION_MODE=danger-full-access
```

### `no sandbox backend is usable` / Bash 工具每次都弹审批

**原因**：容器内没有可用的 sandbox 后端，`workspace-write` 模式起不来；`approval=ask` 时每个命令都要点确认。

**解决**：`DSH_PERMISSION_MODE=danger-full-access` 后审批自动变成 never。
⚠️ 代价是**不再逐条审批**，不要把 3080 暴露到公网。

### `Error: listen EADDRINUSE: address already in use 127.0.0.1:3080`

**解决**：
```bash
pkill -f 'dsh/lib/bin.js'; sleep 2
cd ~ && nohup dsh web > ~/.dsh-web.log 2>&1 &
```

---

## 运行时

### 浏览器打开是白屏

1. 先确认服务活着：`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3080/` → 不是 200 就是服务没起来，看 `~/.dsh-web.log`
2. 服务正常还白屏 → 浏览器内核问题。部分 App 内置 WebView 的 Canvas/WebGL 支持不完整，**DOM 和交互其实正常**，换 Chrome 打开即可

### 页面能开但对话不动 / 一直转圈

**原因**：手机内存紧张时后台标签页被系统回收，前端和服务的连接断了。
**解决**：刷新页面；把长任务拆成小步；关掉其他 App。

### `Operation not permitted` 写文件失败

**原因**：PRoot 视图不一致，不是权限问题（`/root` 里尤其容易）。

**解决**：把工作区换成挂载出来的共享目录：
```bash
mkdir -p /sdcard/Documents/dsh-workspace    # 或你容器里对应的挂载点
```
然后在 web UI 里把工作区指向它。

### App 退到后台就被杀

**原因**：`nohup` 只防 SIGHUP，宿主进程（App / 容器）被杀，沙箱里的一切都结束。

**解决**：真保活需要前台服务 —— Termux 的 `termux-wake-lock` + 电池优化白名单（厂商设置路径不同）。做不到就把 dsh 当「用的时候才开」的工具。

---

## 网络

### `npm install` 卡住 / 极慢

```bash
npm config set registry https://registry.npmmirror.com
```
首次装依赖约 400-600 MB，手机上千兆宽带也要十几分钟，属于正常。

### 想换成别的 OpenAI 兼容端点

dsh 认 `~/.dsh/.env` 里的配置；具体字段以 dsh 官方文档为准，本仓库只管「能在 musl 上跑起来」这一步。

---

## 还是不行

提 issue 时带上：

1. 上面体检脚本的完整输出
2. 报错原文（**完整**，不要截断）
3. 你用的容器（Minis / `proot-distro` / UserLAnd …）和机型
