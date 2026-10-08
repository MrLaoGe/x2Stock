# XXStock

面向 A 股投资者的开源研究工作台，逐步构建 **多 Agent 研究分析 → 量化验证 → 可审计执行** 的能力。

**当前状态：阶段 0，设计文档与开发运维仓库。** 已实现可配置的 Git 推送到 VChat / VoceChat 通知；尚无可运行网页、采集服务、迁移程序或交易功能。架构、业务接口和应用部署描述是后续开发契约，不代表已经实现。

## 项目交流群

- 私域交流群：[https://qq.mctop1.com/](https://qq.mctop1.com/)
- QQ交流群：1126775948

## 项目原则

- 每位使用者独立部署，自行提供 Tushare 与 AI 配置；首期单用户，数据访问边界预留多用户。
- 新项目与 ReviewStock_Codex 的数据库、目录、配置和调度器独立；只在明确的本地迁移操作中只读访问旧数据。
- 支持的数据源仅为 Tushare、东方财富、财联社；排除 zhitu、mairuiapi 的接口、配置和历史数据。
- 先统一数据、重建常规研究功能，再逐步加入 Agent、回测、模拟交易和执行能力。
- 展示数据来源、时间、缺失和过期状态；AI 结论需要证据，不将角色投票作为事实证明。

## 阅读入口

| 目标 | 文档 |
| --- | --- |
| 理解项目和本轮边界 | [总体方案](docs/project-plan.md) |
| 查找全部设计文档 | [文档索引](docs/README.md) |
| 理解模块和旧功能归并 | [功能审查清单](docs/modules/catalog.md) |
| 开始下一轮开发 | [数据中心与迁移模块](docs/modules/data-center.md) |
| 数据源和历史数据复用 | [来源能力矩阵](docs/data/sources.md)、[迁移设计](docs/data/migration.md) |
| 多 Agent 接入与交接 | [开发约束](AGENTS.md)、[协作规范](docs/development/collaboration.md) |
| 当前进度 | [任务台账](docs/development/task-ledger.md)、[阶段路线](docs/roadmap.md) |
| 项目 Skill | [组织与注册规则](docs/development/skills.md)、[github-release](.agents/skills/github-release/SKILL.md) |
| 版本与发布 | [发布规范](docs/development/releases.md)、[版本记录](CHANGELOG.md) |
| Git 与发布机器人通知 | [VChat / VoceChat 配置与脱敏](docs/development/git-notifications.md) |

## 技术选型

前端采用 React、TypeScript、Vite、React Router、Ant Design、TanStack Query 和 ECharts；后端采用 Python、FastAPI、Pydantic、SQLAlchemy、Alembic；长期存储采用 PostgreSQL。后台 worker 独立运行，大批量分析按需使用 pandas、Parquet 和 DuckDB。部署基线为 Docker Compose。

具体架构、配置和 API 约束见 [架构设计](docs/architecture.md)、[接口契约](docs/contracts.md) 和 [配置说明](docs/configuration.md)。当前无需安装这些运行依赖，也没有可执行的 Docker Compose 启动命令。

## 校验文档仓库

仅需 Python 3.11+ 与 Git，不需要数据源或 AI 密钥：

```text
python scripts/verify_repository.py
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

校验工具检查受版本管理的公开资产、相对链接、配置示例和常见凭据模式；它不能证明数据源授权或替代人工发布审查。

## 正式发布

版本以根 [VERSION](VERSION) 为准。main 每批已授权发布从 `0.1.0` 起默认 patch 加一；明确用户指定才改变 minor/major，`0.x` 为 prerelease 且非 latest。发布由同一 Actions 工作流先验证、再将标签绑定确切提交并创建 Release、最后通知配置频道（默认 #19）。开发分支与非发布标签继续发送 push 通知。

失败重跑使用原版本，不覆盖冲突 Release；通知状态不明时先核对频道。Skill、工具与工作流的本地交付和外部发布验收分别记录在 [S0-009 交接](docs/development/handoffs/skill-releases.md)。尚无业务应用，版本号不表示 A 股功能已可运行。

## 参与开发

阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [AGENTS.md](AGENTS.md)。每轮只处理约定模块，完成设计、实现和验收后更新台账与交接记录；不把终极交易目标提前塞入数据底座。

## 许可与数据

代码和项目原创文档采用 [MIT](LICENSE)。第三方代码保留原有许可；数据源提供的数据、新闻正文和用户资产不随项目发布，MIT 不授予它们的再分发权。公开样例只使用明确标注的合成数据。
