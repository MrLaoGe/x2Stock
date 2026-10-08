# x2Stock 界面设计基线

状态：Windows Electron EXE 是产品入口和验收基线；本轮实现空白工作台与独立界面规范预览，金融业务未实现。采用用户指定的 **macos-vibrancy**；localhost 浏览器仅供开发和视觉调试，不是独立 Web 产品。决策见 [ADR 0007](adr/0007-frontend-style.md)。

## 实际入口与范围

- 工作台 `/`：x2Stock 品牌、中文导航、真实空状态。没有行情、报告、业务模块列表或假可用操作。
- 规范预览 `/style-preview`：少量中性按钮、输入、选择、状态与表格示例；仅用于界面规范查看，交互在当前页面内有效，不保存业务设置或发送请求。

Hash 路由在开发地址后使用 `#/style-preview`。未来模块目录是候选规划，未实现模块不出现在产品导航；仅用户选择且通过业务验收后添加入口。不要为凑三栏、图表或指标制造内容。

## 单一风格来源

实际颜色、文字透明度、字体、圆角、边界及过渡变量只维护于 [canonical tokens.css](../frontend/src/styles/tokens.css)。布局见 [AppShell](../frontend/src/components/AppShell.tsx)，基础控件见 [ui.tsx](../frontend/src/components/ui.tsx)，受控样式见 [app.css](../frontend/src/styles/app.css)。新增页面先复用这些资产；本规范说明语义，不建立第二套可独立漂移的 token 字典。

深灰由底层、面板、表面三级表达；侧栏半透明并使用约 24px backdrop blur，其余区域实色。桌面按内容需要形成侧栏、目录面板、内容区层级；工作台保持空白，不为三栏添加假模块。平板压缩或折叠目录，手机折叠导航、单列内容，表格在自己的容器内滚动。

标题使用 Georgia、Times New Roman 并补中文衬线回退；正文使用系统 sans 并兼容 Windows 中文；代码使用系统 monospace。正文阅读宽度受控，中文标题与说明保持清晰层级。

## 交互与禁止项

- 边框统一 1px 半透明白，常态白 8%–12%，焦点可用白 25%；可见键盘焦点不依赖颜色差异唯一表达。
- 最大圆角 12px；默认无阴影。禁止渐变、发光、大阴影、装饰动画、hover 上浮、缩放和单侧粗装饰边框。
- 系统强调蓝只用于文字与交互高亮，不用于按钮或面板的大块背景。Hover/active 轻微提亮，过渡仅颜色，200ms ease-out；`prefers-reduced-motion` 关闭过渡。
- 模糊仅用于侧栏；不支持 backdrop-filter 时侧栏回退为实色深灰。不得把全页玻璃卡片作为默认布局。
- 任何可点击项均有实际行为、语义和可访问名称；使用 label、键盘原生控件及适当 live 状态，不以空链接或死按钮填充界面。

## 可读性与参考例外

正文及信息文字按 WCAG AA 4.5:1 验收，不能因参考 white/40 或 placeholder white/30 而降低可读性。当前 canonical 采用普通弱文本白 58%（在最浅表面约 5.02:1），placeholder 白 48% 只用于深色输入背景（在 #1c1c1e 约 4.87:1）；不把较低透明度当作信息文字。验收应记录实际背景与最浅对比度。强调蓝用于导航和交互文本时也检查实际背景对比度。

未来 A 股红涨绿跌是金融语义例外，应同时提供正负号、文字或数值，颜色不成为唯一渠道。本次只展示中性样例，不使用真实/虚构行情证明该语义。

## Windows 桌面目标与持续验收

当前产品是 Windows x64 免安装应用：默认 zip 解压后双击 EXE，不要求管理员权限。EXE 是首要交付和验收基线；浏览器只供开发/视觉调试，不作为独立 Web 产品发布。Electron 本地设置目录与解压位置分离；当前没有 Runtime 自动更新器，也没有可点击的虚构更新状态。未来更新能力须按受信 SemVer/Windows 资产筛选，并在校验、替换、回退失败时继续打开旧版本。Tauri 2 资源对比可作为后续优化研究，不阻塞本轮 EXE 验收。SQLite WAL、SQLAlchemy/Alembic 与 DuckDB/Parquet 是待模块实施的单用户存储候选，PostgreSQL/Docker 保留未来服务器方案。

命令及本机启动见 [前端开发](development/frontend.md)，未来页面创建或修改应用 [frontend-style Skill](../.agents/skills/frontend-style/SKILL.md)。类型检查、构建和样式检查只是部分证据，必须同时真实检查桌面/平板/手机、键盘焦点、控件行为、可读性、reduced-motion、blur 降级及 console。独立 QA 对固定候选验收，不能由作者单独宣布视觉一致。
