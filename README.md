<p align="center">
  <img src="docs/assets/readme-header.jpg" alt="项目趣图" width="270">
</p>

# x2Stock bata内测开发版

面向 A 股投资者的开源研究工作台，逐步构建 **多 Agent 研究分析 → 量化验证 → 可审计执行** 的能力。

**当前状态：Windows EXE 是产品入口，浏览器仅供开发调试。** 空工作台和中性风格预览已实现简体中文、繁體中文、English；无金融模块、采集、迁移、业务 API 或交易。整体项目下载将随附完整 `desktop-runtime/win-x64` 并由根 `启动.bat` 启动，Git LFS 源码归档是否包含真实二进制须经实际远端下载验收；当前状态见[桌面交接](docs/development/handoffs/frontend-style.md)。

开发协作采用老板派单 → 独立 PM → 持久专业对话 → 独立验收 → 已授权发布。可用的 [多对话开发 Skill](.agents/skills/multi-dialogue-development/SKILL.md) 与本地任务/发布协调工具服务开发阶段；[角色与模块覆盖](docs/development/agent-coverage.md) 定义未来金融专责，不代表金融 Agent 已可运行。

## 项目交流群

- 私域交流群：[https://qq.mctop1.com/](https://qq.mctop1.com/)
- QQ交流群：1126775948

## 项目原则

- 每位使用者独立部署；首期单用户，数据访问边界预留多用户。骨架无需旧项目、数据源凭据或 AI 即可启动，启用相应功能时再自行配置。
- 新项目与 ReviewStock_Codex 的数据库、目录、配置和调度器独立；只在明确的本地迁移操作中只读访问旧数据。
- 支持的数据源仅为 Tushare、东方财富、财联社；排除 zhitu、mairuiapi 的接口、配置和历史数据。
- 按独立新项目建设：用户选模块 → 明确新版功能 → 定义所需数据 → 评估旧数据价值 → 按需另批导入。旧 3.0 仅参考，默认不迁移旧数据。
- 下一项本体任务是最小应用骨架；随后由用户逐个选业务模块，依赖只补最小前置。未选模块不建业务表、不部署采集/导入任务。数据中心随已启用模块增长。
- 新采集满足功能即可独立交付，无需等待可选旧迁移；历史缺失与量化限制如实显示。研究 Agent、量化验证和单独授权执行保持长期方向。
- 展示数据来源、时间、缺失和过期状态；AI 结论需要证据，不将角色投票作为事实证明。

## 阅读入口

| 目标 | 文档 |
| --- | --- |
| 理解项目和本轮边界 | [总体方案](docs/project-plan.md) |
| 查找全部设计文档 | [文档索引](docs/README.md) |
| 理解模块和旧功能归并 | [功能审查清单](docs/modules/catalog.md) |
| 开始下一轮开发 | [最小应用骨架（仅规划）](docs/modules/application-skeleton.md) |
| 已选模块的数据管理和可选复用 | [数据中心](docs/modules/data-center.md)、[来源能力矩阵](docs/data/sources.md)、[迁移设计](docs/data/migration.md) |
| 多 Agent 接入与交接 | [开发约束](AGENTS.md)、[协作规范](docs/development/collaboration.md) |
| 当前进度 | [任务台账](docs/development/task-ledger.md)、[阶段路线](docs/roadmap.md) |
| 项目 Skill | [组织与注册规则](docs/development/skills.md)、[github-release](.agents/skills/github-release/SKILL.md) |
| 版本与发布 | [发布规范](docs/development/releases.md)、[版本记录](CHANGELOG.md) |
| Git 与发布机器人通知 | [VChat / VoceChat 配置与脱敏](docs/development/git-notifications.md) |

## 技术选型

Windows 产品采用 React/TypeScript/Vite 渲染层与 Electron x64 壳，资源随项目提供，无 Node/Python/Docker/外置数据库启动前提。Python/FastAPI/SQLAlchemy/Alembic 保留给后续模块；单用户存储优先 SQLite WAL，Parquet/DuckDB 用于按需批量分析，PostgreSQL/Compose 留未来服务器方案。Ant Design/TanStack Query/ECharts 按模块引入，当前不预装。

技术证据见[桌面架构](docs/architecture.md)、[前端开发](docs/development/frontend.md)及[界面规范](docs/ui-design.md)。

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

阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [AGENTS.md](AGENTS.md)。每轮只处理约定模块，完成设计、实现和验收后更新台账与交接记录；不把旧表存在、角色覆盖或共有功能当作实施授权。当前路线见 [ADR 0006](docs/adr/0006-module-first-new-project.md)。

## 许可与数据

代码和项目原创文档采用 [MIT](LICENSE)。第三方代码保留原有许可；数据源提供的数据、新闻正文和用户资产不随项目发布，MIT 不授予它们的再分发权。公开样例只使用明确标注的合成数据。
