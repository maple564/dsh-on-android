# Changelog

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
