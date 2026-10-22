<div align="center">

<img src="../../assets/hero.png" alt="dsh-on-android" width="100%">

# dsh-on-android

**在 Android 手機上跑 DeepSeek Harness（`dsh web`）** —— 不用 root、不用 Termux X11、不編譯 Chromium；在 PRoot + Alpine（musl / aarch64）裡跑通，四個坑已經填平。

[简体中文](../README.md) · [English](README.en.md) · **繁體中文** · [日本語](README.ja.md) · [한국어](README.ko.md)

</div>

---

## 三行指令

```bash
git clone https://github.com/maple564/dsh-on-android.git && cd dsh-on-android
sh install.sh                                  # 依賴 → dsh → 重編譯 node-pty → 固化到 /opt/dsh-harness
export DEEPSEEK_API_KEY=sk-xxxxxxxx            # 或寫進 ~/.dsh/.env（只放這一行）
dsh-go                                         # 開啟 http://127.0.0.1:3080
```

首次進 web UI：點「繼續」→ 選一個可寫目錄做工作區 → 頂部顯示 `DeepSeek-V4-Flash` 即接通。

![終端實錄](https://github.com/maple564/dsh-on-android/raw/main/assets/terminal.png)

---

## 跑在什麼上面

首次跑通的環境是 **[OpenMinis](https://github.com/OpenMinis/OpenMinis)（即 Minis，開源，GPLv3）**：把手機變成 AI Agent 的 App，自帶完整的 Alpine Linux 沙箱，而那個沙箱本身就是 PRoot + musl + aarch64 —— 正是這個倉庫要對付的環境。

- **在 OpenMinis 裡**：裝好 App，開任意會話，讓 Agent 執行 `sh install.sh` 即可；沙箱、`android-*` CLI、檔案掛載都是現成的（`/var/minis/mounts/...`、`/sdcard/Documents`）。
- **不在 OpenMinis 裡**：Termux + `proot-distro install alpine`、UserLAnd 等任何 PRoot 容器都適用；`install.sh` 只依賴 `apk`、`npm`、`node-gyp`。

---

## 分工：Minis 管本地檔案，dsh 管執行任務

<p align="center"><img src="https://github.com/maple564/dsh-on-android/raw/main/docs/layers.svg" alt="分層" width="100%"></p>

這不是「把 dsh 裝進手機」，而是**兩層各幹一件事**：

| | Minis（本地層） | dsh（執行層） |
|---|---|---|
| 負責 | 掛載手機儲存、PRoot/Alpine 沙箱、裝置能力（相簿/行事曆/通知/剪貼簿）、API key 與權限、App 生命週期 | agent 迴圈、plan/todo 拆解、工具呼叫、長任務上下文、對話/軌跡雙視圖、模型與推理強度 |
| 不負責 | 怎麼拆任務、跑多少步 | 檔案最後躺在哪、裝置權限從哪來 |
| 保證 | **檔案是真的、裝置是真的** | **任務是真的被做完了**（`1 輪 · 31 步` 這種可數證據） |

兩層之間只有**一個契約：掛載目錄**。好處有四：

1. **各幹擅長的** —— 不逼 Minis 去跑幾十步的 agent 迴圈，也不逼 dsh 去解決「怎麼讀手機相簿」。
2. **檔案就是介面** —— Minis 保證路徑真實、裝置可見；dsh 保證寫進去的東西是對的。沒有同步層、沒有網盤、沒有「再傳一次」。
3. **可觀測** —— Minis 側看 shell 進程與檔案位置，dsh 側看對話、軌跡與步數，出問題立刻知道是哪一層。
4. **可替換** —— 執行層換成任何本地服務（Gradio、Jupyter、自己的 RAG）一樣可行，契約只是「一個目錄 + 一個埠」。

一句話：**Minis 提供現實世界，dsh 提供執行力。**

---

## 稀缺點：它不只是「跑起來了」，它能直接動你手機裡的檔案

電腦上跑 dsh 誰都會。**手機上跑 dsh 的價值不在 dsh，而在於它就坐在你的相簿、下載、微信檔案旁邊。**

OpenMinis 會把手機儲存掛到沙箱裡的固定路徑：

| 手機側 | 沙箱內路徑 | 你平時用來做什麼 |
|---|---|---|
| `/sdcard/Documents` | `/var/minis/mounts/Documents/` | 文件、課件、下載的 PDF |
| `/sdcard/Download` | `/var/minis/mounts/Download/` | 瀏覽器下載、微信存下的檔案 |
| 跨會話共享目錄 | `/var/minis/shared/` | 多個會話共用的產物 |

把 dsh 工作區指向這些掛載目錄，它就變成「**能讀寫手機的 Agent**」：

- **產出直接落地手機**：harness 生成的 PPTX / PDF / ICS / 腳本寫進 `Documents/dsh-workspace/`，離開 App 後用檔案管理器、微信、WPS 直接開，不需要「再傳一次到手機」。
- **反向讀手機檔案**：把 `.docx`、課表截圖、發票 PDF 丟進 Documents，讓 dsh 在會話裡直接讀、改、重新匯出。
- **離線 + 私有**：模型走你自己的 API，檔案全程不出裝置。
- **隨時能用**：捷運上、床上、旅行中，不用開電腦。

### 關鍵一步：把工作區掛到掛載目錄

dsh 預設工作區是 `/root`，在 PRoot 裡寫檔容易 `Operation not permitted`，而且手機根本看不到。改成掛載目錄即可。

```bash
mkdir -p /var/minis/mounts/Documents/dsh-workspace
cp ~/.dsh/storages/workspace.json ~/.dsh/storages/workspace.json.bak
python3 - <<'PY'
import json, uuid, datetime
p = json.load(open('/root/.dsh/storages/workspace.json'))
new = "/var/minis/mounts/Documents/dsh-workspace"
for ws in p["tables"]["workspaces"].values():
    if ws.get("path") == new:
        raise SystemExit("已註冊，跳過")
now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", ".000Z")
wid = "ws-" + uuid.uuid4().hex[:12]
p["tables"]["workspaces"][wid] = {"path": new, "title": "dsh-workspace",
                                  "sessionIds": [], "createdAt": now, "updatedAt": now}
p["global"]["workspaceIds"].append(wid)
json.dump(p, open('/root/.dsh/storages/workspace.json', 'w'), indent=2, ensure_ascii=False)
print("註冊成功", wid)
PY
pkill -f 'dsh/lib/bin.js'; sleep 2; dsh-go
```

**驗證**：在新會話裡讓 agent 寫一個 `hello.txt`，然後用手機檔案管理器打開 `Documents/dsh-workspace/` —— 檔案就在那裡。

---

## 為什麼需要這個倉庫

`npx @deepseek-ai/dsh` 在 glibc 桌面是一行指令的事，在 musl 環境會連撞四道牆 —— 而且**每一道牆的報錯都指向錯誤方向**，能讓人白折騰兩天。

| # | 你會看到的報錯 | 你以為的原因 | 真正原因 | 解法 |
|---|---|---|---|---|
| 1 | `Error loading shared library ld-linux-aarch64.so.1` | 缺系統函式庫 | node-pty 拿的是 **glibc 預編譯包** | `node-gyp rebuild` |
| 2 | `--expose-internals is required for HMR` | 參數沒生效 | 該參數**不允許出現在 `NODE_OPTIONS`** | 只能命令列傳給 node |
| 3 | `.env sets DSH_PERMISSION_MODE ... only the launching environment may set` | .env 格式寫錯 | 它是 **bootstrap 變數** | 在 wrapper 裡 `export` |
| 4 | `no sandbox backend is usable` | 權限不夠 | 容器內 workspace-write 無可用後端 | `DSH_PERMISSION_MODE=danger-full-access` |

這個倉庫把四條解法固化成 `install.sh` + 兩個 wrapper。

---

## 環境需求

| 項 | 要求 |
|---|---|
| 宿主 | Android 10+（實測 Android 16 / aarch64） |
| 容器 | 任意 PRoot Linux：**OpenMinis / Minis 沙箱**、`proot-distro install alpine`、UserLAnd 等 |
| 發行版 | Alpine 3.20+（musl）；glibc 發行版自動跳過重編譯 |
| Node | ≥ 20（實測 22.23.2） |
| 磁碟 | 約 800 MB |
| Root | **不需要** |

---

## 四個坑的細節

**1. node-pty 必須針對 musl 重編譯**
```bash
apk add --no-cache build-base linux-headers python3
cd <node_modules>/node-pty && npx --yes node-gyp rebuild     # 看到 "gyp info ok"
```
`prebuilds/linux-arm64/pty.node` 是 glibc ABI，musl 沒有 `ld-linux-aarch64.so.1`，必定載入失敗。

**2. `--expose-internals` 只能走命令列**
```sh
exec node --expose-internals /opt/dsh-harness/node_modules/@deepseek-ai/dsh/lib/bin.js "$@"
```
放進 `NODE_OPTIONS` 會被 Node 直接拒絕；放進 `.env` 無效。

**3. `DSH_PERMISSION_MODE` 是 bootstrap 變數**
```sh
export DSH_PERMISSION_MODE=danger-full-access    # 必須在啟動進程的環境裡
```
寫進 `~/.dsh/.env` 會讓 **dsh 拒絕啟動**（刻意設計）。代價：full-access 模式下**不再逐條審批** Bash 指令，請勿把 3080 暴露到公網。

**4. 固化安裝：PRoot 下 `cp -a` 會失敗，要用 tar 流**
```bash
cd /root/.npm/_npx/<hash>/node_modules
tar cf - --exclude='node-pty/build' . | (cd /opt/dsh-harness && tar xf -)
```
複製完要把鋪平的目錄再包一層 `node_modules/`，`install.sh` 已處理。

---

## 常用指令

| 指令 | 作用 |
|---|---|
| `dsh --version` | 檢查安裝 |
| `dsh-go` | 啟動 web UI 並開啟 |
| `dsh-go --status` | 只看是否在跑 |
| `dsh-go --browser` | 用系統瀏覽器開啟 |
| `pkill -f 'dsh/lib/bin.js'` | 停止 |
| `~/.dsh-web.log` | 日誌 |

---

## 常見問題

**裝完 `dsh --version` 報 `Cannot find module`** —— 目錄層級被鋪平了，必須是 `/opt/dsh-harness/node_modules/@deepseek-ai/dsh/lib/bin.js`。

**web UI 白屏** —— ① 瀏覽器核心 Canvas/WebGL 支援不完整（部分 App 內建 WebView 會白屏但 DOM 與互動正常，換 Chrome）；② 服務沒起來：`curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3080/`，`000` 就是沒啟動。

**寫檔 `Operation not permitted`** —— PRoot 視圖不一致，不是權限問題；把工作區換到掛載的共享目錄。

**App 退到背景就被殺** —— `nohup` 只防 SIGHUP，真要保活得靠 Termux 前台服務 + 電池白名單。

**可以在原生 Termux（不裝 PRoot）跑嗎** —— 可以，而且更穩（bionic 有完整 syscall），但 node-pty 仍需針對該環境編譯。

---

## 已知限制

- **進程生命週期綁宿主**：Android 殺 App／容器，dsh 一起消失，長任務建議拆小步。
- **長會話會被回收**：記憶體緊張時瀏覽器分頁被系統銷毀，前端連線中斷，重新整理即可。
- **效能**：PRoot 有 syscall 轉譯開銷，首次 `npm install` 明顯慢於桌面。
- **不要在公網暴露 3080**：預設 full-access，等於把 shell 交出去。

---

## 貢獻

踩到新坑、換機型跑通、適配其他 PRoot 發行版，都歡迎提 PR。提 issue 請附 `uname -a`、`node -v`、`dsh --version` 與完整報錯原文。

## 授權

[MIT](../../LICENSE)
