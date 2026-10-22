# Changelog

## v0.1.7 — 2026-10-22

### Changed
- **首屏改造**：README 第二屏直接放「你以为的 dsh on Android vs 实际」四行对比表（浏览器 / 电脑 / 云 / Minis 沙箱：谁能碰到你手机的文件、要不要上传、有没有设备能力）
- 仓库 About 改成一句钩子：*别人的 Agent，跑在你手机的文件上：dsh 装在 Minis 的 Alpine 沙箱里，工作区指向你自己的 Documents —— 不上传，文件不出设备*
- 理由：GitHub 在电脑上把文件列表排在 README 前面，About 那 40 个字才是真正的"首屏文案"，它决定路人知不知道这个仓库的差异点

## v0.1.6 — 2026-10-22

### Fixed
- **`install.sh` 漏搬隐藏项**：`for f in *` 不匹配 `.bin` / `.package-lock.json`，固化后 npm 的 bin 链接会丢。改成同时匹配 `.[!.]*`
- 固化后增加一次关键文件存在性检查，路径不对就直接报错，而不是等到运行时 `Cannot find module`

### Added
- `DSH_SRC` / `DSH_SKIP_BUILD=1` / `DSH_BIN_DIR` 三个参数，让脚本可以离线干跑（不重新 npm install 也能验证 tar 固化与 wrapper 生成）
- 已实测：`DSH_SRC=... DSH_SKIP_BUILD=1 DSH_BIN_DIR=/tmp/bin sh install.sh /tmp/opt-test` → 结构正确、`dsh --version` 打出固化那份的版本号、失败时打印 issue 引导

## v0.1.5 — 2026-10-22

### Changed
- 主线重写为**两层分工**：Minis 管本地文件（挂载 / 设备 / 权限 / 生命周期），dsh 管执行任务（agent 循环 / 工具调用 / 步数）；两层之间只有一个契约 —— 挂载目录
- 新增 `docs/layers.svg` 分层图；README 四种语言同步该章节
- 发帖草稿改成以「分工」开场

## v0.1.4 — 2026-10-22

### Added
- **真机实测截图**（Android 16 / Chrome，非示意图）：工作区界面、真实会话（对话/轨迹、产物、任务、31 步）、以及 `dsh-go --status` 里那句 `node --expose-internals ...` 的实证
- README（中/英）新增「真机实测」小节

## v0.1.3 — 2026-10-22

### Added
- **多语言 README**：English / 繁體中文 / 日本語 / 한국어（主 README 简体中文），顶部语言切换栏互链
- **「稀缺点」一节**：dsh 工作区挂到 OpenMinis 的挂载目录（`/var/minis/mounts/Documents` 等）后，Agent 能直接读写手机文件，产物落地后手机文件管理器/微信/WPS 即刻可用；含 `workspace.json` 注册脚本
- `docs/mount-flow.svg`：手机存储 ↔ 沙箱挂载 ↔ dsh 工作区 的数据流示意图

## v0.1.2 — 2026-10-22

### Changed
- 明确标注运行宿主：首次跑通环境是 [OpenMinis / Minis](https://github.com/OpenMinis/OpenMinis)（开源，GPLv3，自带 Alpine 沙箱）
- 新增「跑在什么上面」一节，说明 OpenMinis 与其他 PRoot 容器（`proot-distro` / UserLAnd）的差异与共用点
- 徽章增加 `runs on OpenMinis`

## v0.1.1 — 2026-10-22

### Added
- `assets/` 配图：hero / 终端实录 / 社交预览图（`tools/make_assets.py` 可从真实输出重新生成）
- `docs/pitfalls.md` 排错手册：按「你看到什么」组织，含真实报错原文
- `docs/architecture.svg` 架构图
- README：徽章、TL;DR、四坑折叠详情、FAQ、环境要求表、英文摘要

### Changed
- README 全面重写，突出「四堵墙」这个核心价值
- `install.sh`：编译段与固化段分离，失败时给出明确下一步

## v0.1.0 — 2026-10-22

首次跑通：Android 16 / aarch64 / Alpine (musl) / Node 22.23.2 / dsh 0.1.0-rc.7

### Added
- `install.sh`：依赖 → 安装 dsh → 重编译 node-pty（musl）→ tar 流固化到 `/opt/dsh-harness`
- `dsh` wrapper（`--expose-internals` + `DSH_PERMISSION_MODE`）
- `dsh-go`：启动 web UI 并打开浏览器，支持 `--status` / `--browser`
