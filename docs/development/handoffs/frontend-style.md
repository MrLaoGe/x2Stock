# UI-001：x2Stock Windows EXE 产品首包与固定前端风格交接

## 任务

- 日期：2026-10-08；主文档分支：`codex/frontend-style`。
- 目标：交付 Windows x64 免安装 EXE 空白工作台、三语 UI、固定前端风格 Skill、完整项目分发校验及 GitHub 更新闭环。
- 产品边界：Windows EXE 是产品本身及验收基线。React/Vite 浏览器运行仅供开发和视觉调试，不承诺独立 Web 部署。无行情、API、worker、数据库、采集、迁移、交易或真实用户数据。
- 正式范围：C不自行推送或占用版本；A汇集A/B/C最终候选及独立审查后统一正式main批次。旧preview ZIP仅留审计，常规交付改为完整项目树。

## 当前集成状态

C ready=false（最终固定集成候选独审进行中）。已经合入B最终路线候选及A协作能力、更名决策，受保护A/B文件与ADR0006/0009完整保留；没有推送、升VERSION、标签或新版Release。更新UI与桌面更新器已实现，四项Windows helper实机闭环通过；完整C重建runtime已暂存LFS，仍须最终exact SHA独审闭合。外部状态不会由本地通过改为成功。

| 项目 | 当前结果 | 验收边界 |
| --- | --- | --- |
| 源码集成 | clean构建源`7a4e1ecf7c65e1fcf91cea1aa834e40a09510c38`；桌面final b5ef7ee已整体集成 | 最终二进制/交接提交及独审收据绑定于对话报告，编译清单build SHA不冒充最终tag |
| 整体分发结构 | 根BAT UTF8/CRLF原字节通过-text保存到Git archive；相对启动mainEXE及固定.recovery fallback | 无npm/下载；真实temp中文空格路径BAT smoke通过，新profile简体/273chars/localasar/bridge；ChromiumDNS及Nodeupdater离线拒绝实测 |
| 公共runtime准入 | 共享73资源清单、LFS index/object、x64 PE、VERSION、canonical Git blob源码身份与build祖先 | materialized及LFSfsck通过；13runtime/archive合成测试通过，包含真实gitarchive CRLF回归；不是远端项目下载验收 |
| 归档安全 | 拒LFS pointer、私有配置/数据库、路径碰撞/ADS/设备/遍历，绑定BAT/源码hash/exactSHA前缀 | CI已实现actualarchive→BAT→metadata artifact门槛；实际Actions未运行 |
| 更新工程 | Release筛选/同Release9字段metadata digest/整archive安全解压/用户确认/独立helper与恢复已实现 | healthy、blank rollback、backed-up及awaiting-health kill点BAT恢复实测通过，退出5s后native可见Responding/CDP非空/en偏好、hash/env保留；真实跨版本Release更新仍未验 |
| 架构与性能 | Electron三次warm启动/工作集证据、Python/SQLite/DuckDB未来设计已整理 | 不是cold start/首帧/峰值/private bytes或Tauri实测对比，见[测量证据](../desktop-architecture-evidence.md) |
| GitHub Include LFS | **外部待验收** | 尚无真实exactSHA source archive含全部二进制、BAT离线非空renderer的下载证据，不能标已验收 |
| 真实Release | **外部待验收** | 唯一metadata publisher及notify gate已实现并9项合成测试通过；现有v0.1.0无更新资产，尚无实际跨版本安装证据 |

最终提交之后由独立QA生成exact SHA收据，路径与完整测试结果在对话报告，避免为补写最终SHA再造发布提交。已验收scoped收据位于本机`E:/XXStock/.local/artifacts/windows-preview/architecture-qa`；final验收另存`final-updater`。最终main升patch由A执行，VERSION变化必须重建runtime并再次匹配sourcehash，不能直接用本地0.1.0候选当新版。

实机场景为相同版本的合成runtime事务与真实Windows进程中断，不是物理断电或真实GitHub跨版本更新。无旧profile首装已由隔离新profile BAT实测补齐；物理文字/系统缩放与原生整窗截图仍未验证。未签名，GitHub资产摘要/TLS不是独立发布者签名。

## 首包历史状态（源5554d196，非最终更新候选）

| 能力 | 状态 | 证据或待办 |
| --- | --- | --- |
| 空白工作台与风格规范预览 | 已实现 | React/TypeScript/Vite；业务功能为空 |
| zh-CN / zh-TW / en | 已实现，桌面验收待完成 | zh-CN 默认；切换即时生效并持久化；title、状态、控件及无障碍文案本地化；不依赖远程字体或翻译服务 |
| 前端最终候选 | 已更名，合入文档分支 | `91ebb8da35aebe54be9f5b16550014f0cfe9b5b7`；x2Stock 品牌/三语/title/npm 包，兼容旧语言偏好；保留 Vite 相对 base；桌面新包待构建 |
| 固定风格 Skill | 已实现 | `.agents/skills/frontend-style/SKILL.md` 已登记并通过 Skill 校验 |
| Windows portable 包 | 本地交付完成 | 源 `5554d196eb46fdaf97dbb23f15b51279a9d2b54f` / `codex/desktop-shell-final`，x2Stock.exe/appId/npm/bridge/环境命名均已同步；实体 E:\XXStock/worktree 不改动；已有 AppData/profile 安全复用 |
| 独立 Windows EXE QA | 通过以下已列项目 | 精确新名 ZIP 的 hash/结构/品牌/属性/title/语言迁移/三语/重启/离线/390px 与 renderer 页面截图通过；物理系统缩放及原生整窗截图未验收 |
| Runtime 自动更新器 | 未实现 | 没有 Release 查询、下载、校验、替换、回退或更新 UI |
| 独立 Web 产品 / 正式 Release | 本轮不交付 | localhost 只供开发与视觉调试；无 Web 发布，也无正式版本、标签或 Release |

## 首包历史实现和验证边界

本地交付：`E:\XXStock\.local\artifacts\windows-preview\x2Stock-preview-5554d196-win-x64.zip`，158,298,900 bytes，SHA-256 前缀 `6a689f58880b8eb56`（完整摘要见随包 `.sha256` sidecar）。72 entries / 385,691,644 expanded bytes；解压后的 `x2Stock.exe` 为 246,302,208 bytes，包内无 `XXStock.exe`。独立 QA 在中文空格路径、DNS 阻断条件下确认真实 renderer 资源加载与非空正文。包属性 ProductName/FileDescription 为 x2Stock，npm name 为 x2stock，bridge 为 x2stockDesktop，appId 为 com.mrlaoge.x2stock，开发变量为 X2STOCK_DEV_SERVER_URL。EXE 未签名、Runtime 更新器未实现。

仓库已由主任务真实更名为 `https://github.com/MrLaoGe/x2Stock`，origin 指向同名 `.git`；本任务无更新查询/受信仓库代码。主任务负责 ADR 0009，本任务不占用该编号；正式推送仍等待 main 更名和 A→B→桌面顺序，首包仅本地交付。

新包 QA 对工作台、规范页、404 重跑三语/title/meta/控件/提示/无障碍标签，切换即时生效。旧 `en` + 新值缺失时恢复英文并写入新 key，旧值保留；新 `zh-TW` + 旧 `en` 时繁体优先。QA 保存并恢复两个测试 key 的原值，无 profile 删除或数据覆盖。`CloseMainWindow` 正常退出后从同一路径重启保持英文，原生 title 为 `x2Stock | Workspace`；繁体/简体规范 title 也实测通过。所有 QA 启动进程已关闭。

新名截图目录为 `E:\XXStock\.local\artifacts\windows-preview\screenshots`：`x2Stock-5554d196-zh-CN.png`、`x2Stock-5554d196-zh-TW.png`、`x2Stock-5554d196-en.png`、`x2Stock-5554d196-en-390.png`。它们由 CDP 从精确 ZIP 的 app.asar renderer 捕获并亲自查看，不含原生边框。390px 图在同一连接内设置并核验 innerWidth=390、innerHeight=844、DPR≈1、scrollWidth=clientWidth=375，无横向溢出。物理系统缩放、实际文字缩放、系统级整窗截图未验证；无旧 profile 的首次安装路径仅经源码/合成测试验证。文字对比及 blur fallback 使用此前独立源码检查作为依据。

产品壳采用 Electron Windows x64，加载随包的本地前端并将用户设置写入独立用户目录。前端默认 zh-CN；语言选择使用本机设置持久化，启动时恢复；三个词典具有类型约束。前端源代码通过 typecheck、Stylelint、Vite production build 和 `git diff --check`。生产依赖审计为 0 advisories；完整开发依赖审计报告 7 项 Stylelint 依赖链 advisory，升级修复会改变 Stylelint 主版本，暂不作为本轮阻断。

obsolete 候选（已通过旧名包 QA，因更名不交付）：`E:\XXStock\.local\artifacts\windows-preview\XXStock-preview-a96db3b0-win-x64.zip`，158,298,639 bytes，SHA-256 前缀 `10b41503e94a6e79`（完整摘要保存在随包 `.sha256` sidecar）。ZIP CRC（72 entries / 385,691,120 expanded bytes）、DNS 阻断启动及 CDP packaged renderer 内容均通过。独立 QA 通过三语三路由、控件/提示/无障碍、即时切换与英文退出重启恢复、390px 同会话页面捕获；旧截图保留于 `E:\XXStock\.local\artifacts\windows-preview\screenshots`。截图来自 app.asar renderer，不含原生边框；物理系统缩放/实际文字缩放未验收。旧 EXE 未签名。

失败候选（保留，不交付）：`E:\XXStock\.local\artifacts\windows-preview\XXStock-preview-33c9d506-win-x64.zip`，158,298,636 bytes，SHA-256 前缀 `2a0ba44beeb09989`（完整摘要保存在 sidecar）。其 CDP 结果证明根相对 `/assets/...` 会解析为 `file:///C:/assets/...`，React root 与正文为空；修复是在 `frontend/vite.config.ts` 为打包产物设置相对 `base: './'`。不得用该包的窗口启动记录替代 UI 验收。EXE 未签名。

生产依赖审计 `npm audit --omit=dev` 无 advisories。完整 desktop 构建依赖审计有 8 项 moderate，处于 `electron-builder` 构建依赖链；建议修复版本会将已锁定的 26.15.3 降级，故未改锁文件。审计不能替代 Electron/Chromium 二进制的安全更新检查。Electron/Tauri 性能对比和自动更新安全链路均未验收。不得把早期失效包的启动记录或截图冒充新包验收证据。

## 首包原交接（保留审计，当前后续以集成状态为准）

本地首包交付与独立 QA 已完成。正式集成须基于 B 最新 main，保留主任务更名补丁 `a1dcf4f9c24f740681344566cfc28f16546ebfd4`、ADR 0009 和 2 项新增发布行为测试；顺序仍是 A→B→桌面。当前没有正式 push/tag/Release，未占用正式版本。保留全部旧产物。Runtime 更新器、物理缩放与原生整窗截图分别留给后续实现/验收，不把它们写成当前能力。
