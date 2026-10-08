# ADR 0007：初始界面、三语资源与 Windows 预览壳

日期：2026-10-08；状态：已接受初始视觉、三语交互规范及 Windows EXE 产品入口；Electron 用于当前首包。

## 背景

用户授权先实现没有业务模块的 Windows x64 免安装 EXE，并指定 macos-vibrancy 风格。桌面 EXE 是产品本身和验收基线；React/Vite 浏览器入口只供开发和视觉调试，不作为独立部署的 Web 产品。本首包提供简体中文、繁體中文、English 三种本地 UI 文案，不引入行情、API、worker、数据库、采集、迁移、交易或运行时自动更新能力。

## 决策

React、TypeScript 与 Vite 实现桌面 EXE 内的空白工作台及独立界面规范预览。`localhost` 仅供开发与视觉调试，不形成 Web 产品承诺。界面视觉值由 [tokens.css](../../frontend/src/styles/tokens.css) 单一维护；布局与基础组件是扩展入口；[frontend-style Skill](../../.agents/skills/frontend-style/SKILL.md) 约束后续页面与组件。

所有用户可见文案统一收敛在带类型的 `zh-CN`、`zh-TW`、`en` 词典；默认简体中文，语言入口展示“简体中文 / 繁體中文 / English”，选择立即生效并持久化到本机设置，重启恢复。无效或缺失时默认简体中文。窗口标题、无障碍名称、控件、状态和错误文案跟随当前语言；品牌 `x2Stock` 与版本标识不翻译。简繁中文使用系统字体回退，不下载远程字体。语言不影响时间、单位和数据契约。

本轮采用 Electron 实现 Windows portable EXE，使用受限 renderer 与本地随包页面，用户配置目录与解压目录分离。Electron 是当前产品壳；与 Tauri 的资源性能比较不是本轮交付或产品验收前提，可作为后续优化研究。

用户随后确定项目更名为 `x2Stock`；新 EXE、包名、title、appId、三语品牌、Skill 与新增配置标识同步新名。实体 `E:\XXStock` 与 worktree 路径不批量更名，旧包作为 obsolete 审计保留。已有 `%APPDATA%\XXStock` profile/session 安全复用且不删除；新安装使用 `%APPDATA%\x2Stock`。新语言 key 优先，缺省时只读兼容旧 key；这属于保留真实用户设置的例外，不表示新产品继续使用旧品牌。

## 影响与验收

首包验收以实际 Windows x64 EXE 为准，检查离线启动、三语切换和持久化、窗口标题、长文案/窄窗与缩放；浏览器检查只辅助调试。它不代表正式 Release 或完整应用。Runtime 自动更新器、Release 查询、下载与校验、回退均未实现；后续开发前须另行验证受信发布、签名/完整性、原子切换、用户数据保留和失败恢复。正式分发机制另行验收，当前本地 preview ZIP 不占用正式版本或标签。

Electron 主进程启用 `contextIsolation`、sandbox、禁用 renderer Node，限制 IPC 与导航，并移除无需的菜单。独立 QA 真实检查默认简体、繁体与英语可用视图和控件、立即切换、重启持久化、原生窗口标题、离线启动、英文长文案窄窗与缩放；无法检查的真实窗口截图等项目如实记录。Ant Design 仍是后续选项，接入必须经统一主题适配。
