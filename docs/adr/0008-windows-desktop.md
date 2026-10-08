# ADR 0008：Windows 项目树运行时、桌面技术与更新边界

日期：2026-10-08；状态：架构决策接受，实现与远端归档/更新验收见UI-001交接。补充ADR0007，替代ADR0002当前单用户Web/Compose/PG先决条件；保留ADR0006逐模块路线及ADR0009更名历史。

## 决策

Windows EXE为正式产品，浏览器仅开发/视觉调试。用户下载整个项目即包含`desktop-runtime/win-x64`完整Electron资源，由根启动BAT相对启动，无安装器/外部Node/Python/Docker/PG要求；旧单独EXE ZIP仅保留审计。受控公开runtime经LFS跟踪、精确白名单/指针/PE/manifest/许可证校验；需GitHub Archives include LFS及真实整项目下载运行证据，未开开关不宣称可用。

当前选择Electron/React，依据独立可运行性及现有暖启动测量；Tauri缺工具链未实测，不作性能优势结论。单用户SQLite WAL+显式Alembic、按需Python onedir+内部FastAPI、单进程DuckDB/Parquet作为后续模块架构，未创建业务数据与服务。PG/Compose只留后续服务器方案。

更新信任固定MrLaoGe/x2Stock Release与TLS/API digest；从受信清单下载exactSHA整项目archive，仅抽取并整体切换runtime，保留源码/Git/config/profile，用户确认、bounded下载/安全解压/journal/rollback/非空renderer健康门槛。GitHub账号信任不是独立签名；正式发布exactSHA不等于二进制可以嵌入自己的最终commit，使用源treehash和build_source_sha避免循环。

## 验收与未验证

首包5554d196三语/离线/重启/390px已独立通过；更新器真实helper演练、全项目LFS下载和最终统一版本仍在验收。物理系统缩放/无旧profile首次安装真实分支待验。没有这些证据时不宣布C整体ready。证据与机制见[架构](../architecture.md)、[测量](../development/desktop-architecture-evidence.md)、[交接](../development/handoffs/frontend-style.md)。
