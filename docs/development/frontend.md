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
- 本轮 preview 不含 Runtime 自动更新器。未来更新功能只处理受信 GitHub Release，按整数 SemVer 筛选 0.x prerelease、Windows 资产、说明和校验信息；离线、下载、校验、替换失败必须继续打开旧版本。

## 验证

```text
cd frontend
npm ci
npm run typecheck
npm run build
npm run lint:style
```

Windows 本地打包先生成前端产物，再从仓库根进入 desktop。`pack:dir` 会复制 `frontend/dist` 到被忽略的 `desktop/renderer`，使用锁文件中的 Electron/electron-builder 输出 x64 目录包；运行时无需开发工具。

```text
cd desktop
npm ci
npm run pack:dir
cd ..
python desktop/scripts/make_artifact.py
```

本地 preview helper 使用源 Git SHA 命名 ZIP/sidecar，拒绝覆盖同名产物；默认输出 `E:\XXStock\.local\artifacts\windows-preview`。它是开发本地 helper，不是产品的路径依赖或发布器。Windows `file://` 打包必须保留 Vite `base: './'`，Hash 路由与本地资源需在精确 ZIP 的解压副本实际核验，不能只测试 dev server。

产品名为 `x2Stock`，npm/配置标识为 `x2stock` / `X2STOCK`，调试服务环境变量是 `X2STOCK_DEV_SERVER_URL`。新安装写入 `%APPDATA%\x2Stock`；如果旧 `%APPDATA%\XXStock` 已有 profile 或 session，则安全复用该根目录，不复制、不删除、不覆盖资料。不要同时运行旧名和更名包共享同一旧 profile。语言设置以 `x2stock.language` 优先，仅在新值不存在时兼容读取 `xxstock.language`，随后保存新 key，旧 key 保留。

更名兼容行为验证：

```text
cd frontend
npm run test:preferences
cd ../desktop
node --test tests/profile-compat.test.cjs
```

桌面工程还需核对 npm registry 锁定版本、portable 构建、x64 exe 启动和用户数据保留。自动更新功能开发后，另验更新检测/确认、下载完整性、原子替换与失败回退。没有真实 Windows 或签名条件时，明确记录未验证。仓库根运行 python scripts/verify_repository.py、python -m unittest discover -s tests -p 'test_*.py' 与 git diff --check。样式和单元测试不能替代真实桌面与浏览器检查。

独立 QA 以真实 Windows EXE 验收简体中文默认、繁体中文与英文切换、窗口标题一致、重启恢复、离线运行和英文长文本在缩放/窄窗下不裁切。浏览器不能替代这组检查。当前没有更新界面或 Runtime 更新器，不得展示可点击的假更新操作。
