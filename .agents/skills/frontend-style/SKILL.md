---
name: frontend-style
description: 创建、修改或评审 XXStock 的任何前端页面、布局与组件时使用，复用项目 macos-vibrancy token 和基础组件，保持视觉与交互一致。只处理项目网页风格，不扩展业务模块、数据访问或发布权限。
---

# XXStock 前端风格

把已定稿的 macos-vibrancy 应用于当前获授权的页面需求。新增业务仍由对应模块任务决定；风格示例不构成业务实现许可。

## 先读真实基线

- [tokens.css](../../../frontend/src/styles/tokens.css)：颜色、字体、间距、边框、圆角、过渡和布局 token 的唯一值源。直接使用 CSS 变量，不在页面、Skill 或 TS 主题中另抄一套值。
- [基础组件](../../../frontend/src/components/ui.tsx)、[AppShell](../../../frontend/src/components/AppShell.tsx) 与 [全局样式](../../../frontend/src/styles/app.css)：先复用现有实现，再决定是否需要扩展。
- [界面规范](../../../docs/ui-design.md)：布局、可读性与获批准的语义例外；[前端开发说明](../../../docs/development/frontend.md)：运行、目录和校验约定。
- [空工作台](../../../frontend/src/pages/WorkspacePage.tsx) 与 [界面规范预览](../../../frontend/src/pages/StylePreviewPage.tsx)：真实页面基线。预览页是中性组件示例，不是业务设置入口。

相对路径均从本 Skill 目录解析。先核对文件实际内容；路径失效时查找当前入口并修复引用，不能按记忆补造组件 API。

## 必须保持的风格

- 用 canonical 深、中、浅三级灰表现面板层级；蓝色只作文字或交互高亮，不作按钮、卡片等大块背景。默认无阴影；禁止渐变、发光、装饰动画、hover 上浮或缩放。
- vibrancy 只用于 AppShell 侧栏，复用其半透明深灰与模糊 token；其他面板为纯色。保留不支持 `backdrop-filter` 时的实色降级，不做满页玻璃卡片。
- 分隔与控件边框为 1px 半透明白，复用正常边框和焦点 token；圆角不超过 12px。焦点可提高白色边框可见度，并保留清晰的键盘焦点轮廓。
- 标题沿用 Georgia / Times New Roman 与中文衬线回退；正文用含 Windows 中文回退的系统 sans；代码用 monospace。不要引入另套字体或品牌视觉。
- hover/active 仅轻提亮。过渡为 200ms ease-out，只作用于颜色属性，不能使用 `transition: all`；保留 `prefers-reduced-motion` 降级。
- 文字在实际底色与透明合成结果上满足 WCAG AA：普通文字至少 4.5:1，大字至少 3:1。不要复原参考中的低对比弱文字或占位透明度；使用已提高可读性的 token，并在界面规范记录必要例外。状态同时提供文字或符号，不能只用颜色表达。
- 桌面按任务内容使用侧栏、上下文面板与内容区，不为凑三栏添加假内容。平板和手机折叠侧栏与次要面板；页面不横向溢出，确有需要的表格在自身容器滚动。控件保留标签、可访问名称和键盘行为。

未来获授权金融模块可使用规范中的红涨绿跌语义例外，同时给出正负号、文字或数值；本初始风格页不制造金融样本。参考文件中的彩色背景与阴影示例服从上述禁止项；其泛化玻璃态禁令不取消已选侧栏 vibrancy。

## 扩展方法

1. 从现有组件与 AppShell 组合当前需求；补充语义化页面样式，引用 canonical 变量。初始首页保持真实空状态，不列出假装可用的模块、死链接或无行为按钮。
2. 新共享视觉角色确有需要时，在 `tokens.css` 增加语义 token；同步组件与界面规范，说明用途、对比度和例外。不要为了一个页面新增局部色板、复制 token 文件或堆叠临时 override。
3. 若引入 Ant Design，通过统一 ConfigProvider/theme 和受控适配接入 canonical token；主题映射读取变量，不硬编码副本。实际检查弹层、焦点、选中、禁用、hover 等状态，不能直接沿用组件库彩色主按钮与阴影默认值。
4. 新控件实现需求明确的行为、错误与空状态。预览交互明确为视觉示例；新增查询、图表、数据 SDK 或模块导航需对应需求授权。

## 验证与交付

在 `frontend/` 执行：

```text
npm ci
npm run typecheck
npm run build
npm run lint:style
```

在仓库根执行 `python scripts/verify_repository.py` 与 `git diff --check`；文档/Skill 同步登记，按项目交接规范记录最终状态。修改 Skill 时另运行可用环境的 skill-creator `quick_validate.py`，该开发工具不是网页运行依赖。

开发服务仅监听 `127.0.0.1`；按前端说明检查端口后运行 `npm run dev`，不抢占其他服务。用真实浏览器检查桌面、平板、手机上的页面与实际交互：Tab / Shift+Tab 焦点、Enter / Space 动作、输入与选择反馈、窄屏收纳、文本对比度、reduced-motion 与模糊降级，并检查 console。新增弹层时还检查 Escape、焦点进入及返回。

留下可复核的截图与检查结果，说明浏览器及视口。静态规则或构建通过不能证明视觉一致；复用既有行为测试，只有关键行为变化才增加有价值的回归，不为简单样式添加镜像测试。
