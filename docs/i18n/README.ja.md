<div align="center">

<img src="../../assets/hero.png" alt="dsh-on-android" width="100%">

# dsh-on-android

**Android スマホの [OpenMinis](https://github.com/OpenMinis/OpenMinis)（Minis）上で DeepSeek Harness を動かし、スマホのファイルをワークスペースとしてマウントする。** root 不要、Termux X11 不要、Chromium のビルドも不要 —— PRoot + Alpine（musl / aarch64）の 4 つの罠は解決済み。

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-TW.md) · **日本語** · [한국어](README.ko.md)

</div>

---

## 3 行で始める

```bash
git clone https://github.com/maple564/dsh-on-android.git && cd dsh-on-android
sh install.sh                                  # 依存 → dsh → node-pty 再ビルド → /opt/dsh-harness に固定
export DEEPSEEK_API_KEY=sk-xxxxxxxx            # または ~/.dsh/.env にこの 1 行だけ
dsh-go                                         # http://127.0.0.1:3080 を開く
```

Web UI 初回: 「続行」→ 書き込み可能なワークスペースを選択 → ヘッダに `DeepSeek-V4-Flash` が出れば接続成功。

---

## 何の上で動くか

リファレンス環境は **[OpenMinis](https://github.com/OpenMinis/OpenMinis)（旧 Minis、オープンソース、GPLv3）**。スマホ上に Alpine Linux サンドボックスを載せる AI エージェントアプリで、そのサンドボックスは PRoot + musl + aarch64 —— まさにこのリポジトリが相手にする環境です。

- **OpenMinis 内**: アプリを入れて任意のセッションで `sh install.sh` を実行するだけ。サンドボックス、`android-*` CLI、ファイルマウントは最初から揃っています（`/var/minis/mounts/...`、`/sdcard/Documents`）。
- **それ以外**: Termux + `proot-distro install alpine`、UserLAnd など任意の PRoot コンテナ。`install.sh` が必要とするのは `apk` / `npm` / `node-gyp` だけ。

---

## 役割分担：ローカルファイルは Minis、タスク実行は dsh

<p align="center"><img src="https://github.com/maple564/dsh-on-android/raw/main/docs/layers.svg" alt="二層構造" width="100%"></p>

「dsh をスマホに入れる」話ではなく、**2 つの層がそれぞれ 1 つの仕事をする**話です。

| | Minis（ローカル層） | dsh（実行層） |
|---|---|---|
| 担当 | ストレージのマウント、PRoot/Alpine サンドボックス、端末 API（写真・カレンダー・通知・クリップボード）、API キーと権限、App のライフサイクル | agent ループ、plan/todo の分解、ツール呼び出し、長いタスクの文脈、会話/トレース表示、モデルと推論強度 |
| 担当しない | タスクの分解、何ステップかかるか | ファイルが最終的にどこにあるか、権限の出どころ |
| 保証 | **ファイルは本物、端末も本物** | **タスクが本当に終わっている**（`1 ターン · 31 ステップ` という数えられる証拠） |

両層の契約は**マウントディレクトリ 1 つだけ**。そこから 4 つの利点が出ます。

1. **得意なことをやる** — Minis に 30 ステップの agent ループを走らせず、dsh に「スマホの写真をどう読むか」を解かせない（永久に解けません）。
2. **ファイルがインターフェース** — Minis はパスが本物で端末から見えることを保証し、dsh は書き込まれた中身が正しいことを保証します。同期層もクラウドも「もう一度送る」も不要。
3. **観測できる** — Minis 側でシェルプロセスとファイルの場所、dsh 側で会話・トレース・ステップ数。障害がどちらの層か即座に分かります。
4. **差し替え可能** — 実行層は他のローカルサービス（Gradio、Jupyter、自前の RAG）でも成立します。契約は「ディレクトリ 1 つとポート 1 つ」だけだから。

ひと言で：**Minis が現実世界を、dsh が実行力を提供する。**

---

## 希少な点：動くだけではなく、スマホの中のファイルを直接触れる

ノート PC で dsh を動かすのは誰でもできます。**スマホで動かす価値は dsh 本体ではなく、写真・ダウンロード・チャット添付のすぐ隣にいること**です。

OpenMinis はスマホのストレージを固定パスにマウントします。

| スマホ側 | サンドボックス内 | 使いどころ |
|---|---|---|
| `/sdcard/Documents` | `/var/minis/mounts/Documents/` | 書類、講義資料、DL した PDF |
| `/sdcard/Download` | `/var/minis/mounts/Download/` | ブラウザの DL、WeChat 保存ファイル |
| セッション間共有 | `/var/minis/shared/` | 複数セッションで共有する成果物 |

dsh のワークスペースをここに向ければ、**スマホを読み書きできるエージェント**になります。

- **成果物がそのままスマホに残る** — `Documents/dsh-workspace/` に書いた PPTX / PDF / ICS / スクリプトは、アプリを閉じたあとファイルマネージャや WPS で直接開ける。「もう一度スマホに送る」工程が不要。
- **逆方向も可** — `.docx`、時間割のスクショ、領収書 PDF を Documents に入れておけば、セッション内で読む・直す・再出力できる。
- **オフライン & プライベート** — 推論は自分の API キー、ファイルは端末外に出ない。
- **どこでも使える** — 電車の中でも、ベッドでも、旅行先でも。

### 肝心の 1 ステップ：ワークスペースをマウント先にする

dsh の既定ワークスペースは `/root` で、PRoot では `Operation not permitted` になりがち、しかもスマホから見えません。マウント先に変えます。

```bash
mkdir -p /var/minis/mounts/Documents/dsh-workspace
cp ~/.dsh/storages/workspace.json ~/.dsh/storages/workspace.json.bak
python3 - <<'PY'
import json, uuid, datetime
p = json.load(open('/root/.dsh/storages/workspace.json'))
new = "/var/minis/mounts/Documents/dsh-workspace"
for ws in p["tables"]["workspaces"].values():
    if ws.get("path") == new:
        raise SystemExit("登録済み")
now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", ".000Z")
wid = "ws-" + uuid.uuid4().hex[:12]
p["tables"]["workspaces"][wid] = {"path": new, "title": "dsh-workspace",
                                  "sessionIds": [], "createdAt": now, "updatedAt": now}
p["global"]["workspaceIds"].append(wid)
json.dump(p, open('/root/.dsh/storages/workspace.json', 'w'), indent=2, ensure_ascii=False)
print("登録完了", wid)
PY
pkill -f 'dsh/lib/bin.js'; sleep 2; dsh-go
```

**確認**: 新規セッションで `hello.txt` を書かせ、スマホのファイルマネージャで `Documents/dsh-workspace/` を開く —— あれば成功です。

---

## なぜこのリポジトリが必要か

`npx @deepseek-ai/dsh` は glibc デスクトップなら 1 行。musl では 4 つの壁に連続でぶつかり、しかも**どのエラーメッセージも原因を誤って指します**。

| # | 出るエラー | 思いがちな原因 | 実際の原因 | 対処 |
|---|---|---|---|---|
| 1 | `Error loading shared library ld-linux-aarch64.so.1` | システムライブラリ不足 | node-pty が **glibc 向けプリビルド** | `node-gyp rebuild` |
| 2 | `--expose-internals is required for HMR` | フラグが効いていない | `NODE_OPTIONS` では**許可されない** | node のコマンドラインで渡す |
| 3 | `.env sets DSH_PERMISSION_MODE ... only the launching environment may set` | .env の書式ミス | **bootstrap 変数** | wrapper で `export` |
| 4 | `no sandbox backend is usable` | 権限不足 | コンテナでは workspace-write のバックエンドが無い | `DSH_PERMISSION_MODE=danger-full-access` |

---

## 動作環境

| 項目 | 要件 |
|---|---|
| ホスト | Android 10+（Android 16 / aarch64 で実測） |
| コンテナ | 任意の PRoot Linux: **OpenMinis / Minis サンドボックス**、`proot-distro`、UserLAnd など |
| ディストリ | Alpine 3.20+（musl）。glibc 系は再ビルドを自動スキップ |
| Node | 20 以上（22.23.2 で実測） |
| ディスク | 約 800 MB |
| root | **不要** |

---

## コマンド

| コマンド | 用途 |
|---|---|
| `dsh --version` | インストール確認 |
| `dsh-go` | Web UI を起動して開く |
| `dsh-go --status` | 起動中か確認 |
| `pkill -f 'dsh/lib/bin.js'` | 停止 |
| `~/.dsh-web.log` | ログ |

---

## よくある質問

**`Cannot find module`** — ディレクトリ階層が平坦化されています。`/opt/dsh-harness/node_modules/@deepseek-ai/dsh/lib/bin.js` である必要があります。

**Web UI が真っ白** — ① ブラウザエンジンが Canvas/WebGL 非対応（アプリ内 WebView では白くても DOM は動く。Chrome で開く）② サーバが落ちている: `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3080/` が `000` なら未起動。

**書き込みで `Operation not permitted`** — PRoot のビュー不整合。ワークスペースをマウント先へ。

**バックグラウンドで即殺される** — `nohup` は SIGHUP しか防げません。Termux の常駐サービス + 電池最適化の除外が必要。

---

## 既知の制限

- **プロセス寿命はホスト依存**：アプリ/コンテナが死ねば dsh も死ぬ。長いタスクは分割する。
- **長いセッションは回収される**：メモリ逼迫でタブが破棄され接続が切れる。再読み込みで復帰。
- **性能**：PRoot の syscall 変換コストで初回 `npm install` は遅い。
- **3080 を公開しない**：既定は full-access で、シェルを差し出すのと同じ。

## ライセンス

[MIT](../../LICENSE)
