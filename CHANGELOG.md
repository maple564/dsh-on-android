# Changelog

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
