# 配置与用户接入设计

状态：应用配置为设计；独立 Git 通知工具已实现其 `notifications.vocechat` 子集的读取与脱敏。公开模板为 [config.example.json](../config/config.example.json) 与 [.env.example](../.env.example)。模板不是真实用户配置，也不触发网络访问。

## 配置位置和优先级

普通设置采用“已提供的环境变量 → `config/config.local.json` → 版本化默认值”。缺省使用示例中的设计值；JSON 中的 `*_env` 表示环境变量名称，而非密钥。环境变量空值视为未提供；关闭功能使用明确的 `enabled=false`，不依赖空字符串。

秘密只从后端环境或部署 secrets 读取，不写 JSON。未来 secrets 文件采用对应的 `*_FILE` 环境变量；同一秘密同时配置直接变量和 `_FILE` 时启动报配置冲突，防止意外选错账户。实际文件、`.env`、本地 JSON 和数据目录均被 Git 忽略。

公开 settings 接口返回配置状态、脱敏摘要和验证结果，不返回密钥、数据库密码或完整带凭据 URI。异常日志不能透传 provider 请求体或认证头。

## 运行设置

| 配置 | 默认 | 含义 |
| --- | --- | --- |
| `XXSTOCK_BIND_HOST` | `127.0.0.1` | 单用户仅本机访问 |
| `XXSTOCK_WEB_PORT` | `8080` | 后续生产静态网页与同源 API 代理 |
| `XXSTOCK_API_PORT` | `8140` | 原生开发 API，避开旧服务端口 |
| `XXSTOCK_DEV_WEB_PORT` | `5180` | Vite 开发端口 |
| `XXSTOCK_TIMEZONE` | `Asia/Shanghai` | 交易时段及用户展示时间 |
| `XXSTOCK_LOCAL_USER_ID` / `XXSTOCK_LOCAL_WORKSPACE_ID` | `local` / `local` | 服务端身份上下文；不是访问令牌 |
| `XXSTOCK_DATA_DIR` | `.local/data` | 新版私有数据，不指向旧目录 |
| `DATABASE_URL` | 未配置 | 独立 PostgreSQL，不连接旧库 |

Compose 基线只把 web 映射到 `127.0.0.1:8080`；API、worker、PostgreSQL 使用内部网络。PostgreSQL 容器内为 `5432`，默认不映射到宿主机。密码由使用者设置；不提供公共默认密码。原生开发 API/Vite 也绑定本机，CORS 只开放实际开发来源。

首期不是面向公网的免登录服务。允许外部访问和多人共享前必须实现认证、会话、归属授权及用户 secrets 隔离，不能仅改变 bind host。

## 数据源配置

Tushare 使用 `TUSHARE_TOKEN`，通过 SDK 或固定官方 HTTP 地址访问。缺 token 不导致空数据覆盖，也不自动探测收费数据；在能力列表显示 `missing_credential`。权限核验逐接口、最小请求、显式触发，记录核验时间和结果。

东方财富与财联社适配器也要独立记录端点、口径、限频、最近成功和结构变化；“公开接口”不代表有可保证的 SLA。三类来源开关不能改变准入规则。此阶段不会创建 zhitu、mairuiapi 或其他来源配置。

MCP 是后续 Agent 工具通道，不承担初期持久采集。若接入，带 token 的 URL 从秘密配置即时组装，不进入仓库、前端、日志和 Agent 普通上下文。MCP 的数据仍经过同一契约、缓存和权限核验。

## AI 配置

| 配置 | 默认与行为 |
| --- | --- |
| `AI_ENABLED` | `false`；未配置 AI 仍可使用确定性数据与研究模块 |
| `AI_BASE_URL` | `https://api.openai.com/v1`；由部署者配置 |
| `AI_API_KEY` | 空；仅后端读取 |
| `AI_MODEL` | 空；用户填写 GPT 模型，不硬编码“最新模型” |
| `AI_PROTOCOL` | `responses`，另支持 `chat_completions` |
| `AI_TIMEOUT_SECONDS` | `60` |
| `AI_MAX_CONCURRENT_REQUESTS` | `1`，后续按实测调整 |
| `AI_MAX_OUTPUT_TOKENS` | `2048`，每个角色可在总预算内收紧 |
| `AI_DAILY_BUDGET_CNY` | `0`，默认不开启计费工作 |
| `AI_INPUT_CNY_PER_MILLION_TOKENS` / `AI_OUTPUT_CNY_PER_MILLION_TOKENS` | 空；部署者填写每百万 token 的人民币输入/输出价格 |

启用 AI 需要模型、密钥、非零预算、明确协议以及部署者填写的输入/输出计费参数；缺价格时不能可靠计算费用，禁止计费后台任务并显示待配置。第三方网关的自定义地址不能证明协议完整兼容，需分别验证文本输出、结构化输出和错误处理。

费用在任务发起前按最坏输入/输出上限预占，完结按可得实际用量结算并释放差额；并发任务共享预算计数，重试也计入。缓存输入先按普通输入价格保守估算，不自动下载价格或推测汇率。免费网关可明确填写零价格，仍需要非零预算与显式启用。

不会因 Responses 失败就隐式切换到另一模型或协议重复付费。连接测试属于用户主动操作，显示预期请求和预算，再按已有操作授权执行。模型故障时确定性计算可继续，报告明确标记 AI 未完成。

OpenAI 官方 SDK 支持 Responses 和可配置客户端；第三方兼容性需另行验证，参考 [官方 Python SDK](https://developers.openai.com/api/reference/python)。开发 Codex 的模型设置与产品 AI 配置彼此独立。

## 已实现：VChat / VoceChat Git 通知

机器人地址与密钥分别通过 `VOCECHAT_BASE_URL`、`VOCECHAT_API_KEY` 配置，频道 `VOCECHAT_GROUP_ID` 默认 `19`；公开模板默认关闭且秘密为空。GitHub端使用 Actions Secrets 存地址/密钥、Variables存开关/频道/前缀/超时。配置检查只显示是否已配置，错误不包含上游正文或原始异常。

工具仅为 Git 推送通知，不启动应用服务或旧调度器。使用方法、环境优先级、脱敏及故障验收见 [通知说明](development/git-notifications.md)。

## 迁移配置

`LEGACY_SOURCE_PATH` 默认为空，只供用户主动运行的本地迁移工具使用。正常服务启动不读取它、不扫描旧目录。工具必须验证源、目标不是同一个库或目录，并把只读连接、一致性快照和导入报告作为独立操作。

## 配置验收

验证未配置、不合法、缺凭据、权限不足、协议不兼容、价格缺失与预算耗尽。确认前端、日志、任务错误和导出均无秘密；实际本地配置不会被 `git add .` 纳入。未来具体解析代码和设置界面随数据模块/AI模块实现。


## Windows 首包边界

Windows EXE 是产品入口，浏览器仅用于开发/视觉调试。免安装包解压到用户选择目录；它不启动 Docker、PostgreSQL、Python worker 或外置 API。程序目录、用户数据、未来更新下载临时目录和缓存必须独立，更新不能覆盖研究资产。Runtime 更新器尚未实现；当前首包没有更新 UI 或操作。未来 Release 更新器的签名/完整性公钥可随程序发布，私钥只在 CI secret；渲染器不接触 token。
