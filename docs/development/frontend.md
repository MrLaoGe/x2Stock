# 初始前端与桌面开发

产品入口是 Windows x64 Electron EXE，实际 EXE 是交付与验收基线。React/Vite 浏览器运行仅用于开发和视觉调试，不承诺独立部署的 Web 产品。当前空白工作台没有 API、worker、数据库、采集、迁移或金融业务；业务模块和后端另行批准。

## 研发启动

```text
cd frontend
npm ci
npm run dev
```

开发服务仅绑定 127.0.0.1，默认 5181，使用 strictPort；端口被占用会失败。localhost 只用于研发与视觉调试。桌面调试和打包命令以桌面目录 package.json 为准。

## 扩展入口

- frontend/src/styles/tokens.css 是唯一设计 token 值源。
- AppShell 与基础控件复用给浏览器和 Electron 渲染器；不在组件、Skill 或文档中另建数值副本。
- Electron 使用 contextIsolation/sandbox、nodeIntegration=false、受控 IPC 和受信导航；渲染器不接触 GitHub token、签名私钥或文件替换权限。
- 页面文案来自集中带类型的 `zh-CN`、`zh-TW`、`en` 资源；默认简体中文，语言选择即时生效并持久化到本地设置，重启恢复。无有效值时回到简体中文；品牌名和版本标识不翻译。新增页面需补三语词条并运行缺键检查。
- 语言选择器显示“简体中文 / 繁體中文 / English”。所有错误、确认、空状态、控件标签和无障碍名称跟随当前语言；繁体使用译文。字体用系统简繁中文和英文回退，不依赖远端字体。语言不影响时区、单位或数据契约。
- 更新UI已实现三语状态与确认，桌面更新器正在集成验收；固定受信GitHub Release/整数SemVer/0.x prerelease/同Release metadata及整项目归档，失败保持旧程序。实现与真实远端验收分别见[桌面更新](desktop-updates.md)及[交接](handoffs/frontend-style.md)。

## 验证

```text
cd frontend
npm ci
npm run typecheck
npm run build
npm run lint:style
npm run test:preferences
npm run test:updates
```

Windows 本地打包先生成前端产物，再从仓库根进入 desktop。`pack:dir` 会复制 `frontend/dist` 到被忽略的 `desktop/renderer`，使用锁文件中的 Electron/electron-builder 输出 x64 目录包；运行时无需开发工具。

```text
cd desktop
npm ci
npm test
npm run pack:dir
```

常规交付将`desktop/release/win-unpacked`完整资源放入公开批准的`desktop-runtime/win-x64`，经Git LFS暂存、materialized验证、根BAT及独立QA后再交给A统一发布；不再每版调用旧make_artifact ZIP helper，旧产物保留审计。root VERSION提供打包版本；新版本需重建manifest并与最终源码treehash一致。Windows `file://` 打包保留 Vite `base: './'`，Hash路由与本地资源在精确项目树实际核验，不能只测试dev server。

产品名为 `x2Stock`，npm/配置标识为 `x2stock` / `X2STOCK`，调试服务环境变量是 `X2STOCK_DEV_SERVER_URL`。新安装写入 `%APPDATA%\x2Stock`；如果旧 `%APPDATA%\XXStock` 已有 profile 或 session，则安全复用该根目录，不复制、不删除、不覆盖资料。不要同时运行旧名和更名包共享同一旧 profile。语言设置以 `x2stock.language` 优先，仅在新值不存在时兼容读取 `xxstock.language`，随后保存新 key，旧 key 保留。

更名兼容行为验证：

```text
cd frontend
npm run test:preferences
cd ../desktop
node --test tests/profile-compat.test.cjs
```

桌面工程还核对锁定版本、完整资源、x64 exe启动、用户资料保留以及更新检测/确认、摘要、逐次rename与回退；两次rename不是整体原子替换。Windows进程及中断恢复证据与远端LFS/Release外验分别记录。仓库根运行python scripts/verify_repository.py、Python unittest及git diff --check；暂存runtime后运行python scripts/verify_desktop_runtime.py --materialized，随后python scripts/smoke_project_archive.py --root . 验根BAT。烟测需要研发Node24/Python/Windows，仅使用标记temp副本，产品使用者无需这些工具。

独立 QA 以真实Windows EXE验收简体默认、繁体/英文、title、重启恢复、离线及窄窗/缩放；浏览器不能替代。更新状态与确认来自有限typed IPC，事件订阅跟随组件清理，不获取任意remote URL，不把源码和合成通过写成真实Release更新完成。
