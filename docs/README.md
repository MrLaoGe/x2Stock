# 设计文档索引

当前交付是阶段 0 文档与开发运维仓库；Git通知工具已实现，其他设计不代表相应运行功能已经实现。

## 项目和产品

- [总体方案](project-plan.md)：已确认决策与首轮边界。
- [旧功能参考目录](modules/catalog.md)：用户选模块的参考，不是任务队列。
- [最小应用骨架](modules/application-skeleton.md)：下一项本体任务，只有规划与验收，未实现。
- [界面规范](ui-design.md)：桌面工作台与手机操作原则。
- [阶段路线](roadmap.md)：各阶段交付与进入下一阶段的条件。

- [前端开发](development/frontend.md)：Windows 构建、根 BAT、三语与浏览器调试边界。
- [桌面交接](development/handoffs/frontend-style.md)：精确产物、独立 QA 和外部待验。

## 技术与数据

- [架构设计](architecture.md)：前后端、worker、存储和部署边界。
- [接口契约](contracts.md)：身份、数据状态、时间、口径和来源。
- [配置说明](configuration.md)：用户 AI、Tushare、数据库和本地 secrets。
- [来源能力矩阵](data/sources.md)：允许来源、数据集、权限与核验。
- [旧数据审计](data/legacy-audit.md)：已观察事实、规模和缺口。
- [迁移设计](data/migration.md)：来源过滤、只读导出、幂等和回滚。
- [数据中心](modules/data-center.md)：随已启用模块增长的配置、任务、来源/质量管理；非前置搬库。

## Agent 和多对话维护

- [Agent 设计](agents.md)：开发角色与未来产品研究角色。
- [协作规范](development/collaboration.md)：分支、worktree、评审和集成。
- [多对话开发 Skill](../.agents/skills/multi-dialogue-development/SKILL.md)：老板、PM、专业执行、独立审查与本地协调。
- [逐项角色覆盖](development/agent-coverage.md)：模块能力的业务、实现和独立验收。
- [多对话交接](development/handoffs/multi-dialogue-development.md)：本轮实现、真实演练与外部验收边界。
- [项目 Skill 组织](development/skills.md)：项目目录、注册表、开发/业务分类和权限边界。
- [github-release Skill](../.agents/skills/github-release/SKILL.md)：本地准备/检查和受限 Actions 发布入口。
- [版本与正式发布](development/releases.md)：版本、exact SHA、Release、最终通知与失败恢复。
- [Git 与发布到 VChat / VoceChat](development/git-notifications.md)：通知分工、配置和脱敏。
- [任务台账](development/task-ledger.md)：实际完成状态。
- [交接模板](development/handoff-template.md)：每轮交付的最小交接。
- [阶段 0 交接](development/handoffs/phase-0.md)：本轮已交付内容及下一轮入口。
- [Git 通知交接](development/handoffs/git-notifications.md)：此前真实频道19投递验收与维护。
- [Skill 与发布交接](development/handoffs/skill-releases.md)：本轮本地完成和外部待验收状态。
- [路线调整交接](development/handoffs/module-first-roadmap.md)：本轮文档边界、审查与串行发布依赖。
- [CHANGELOG](../CHANGELOG.md)：正式发布版本索引。

## 已接受的架构决策

- [ADR 0001：独立仓库和阶段推进](adr/0001-project-boundary.md)
- [ADR 0002：技术栈与独立部署](adr/0002-stack-and-deployment.md)
- [ADR 0003：来源准入和历史迁移](adr/0003-provenance-and-migration.md)
- [ADR 0004：Agent 证据与执行边界](adr/0004-agent-and-execution.md)
- [ADR 0005：独立 PM 与持久专业对话](adr/0005-multi-dialogue-development.md)
- [ADR 0006：独立新建与按模块复用](adr/0006-module-first-new-project.md)：替代旧数据中心/迁移优先顺序，保留历史 ADR。

- [ADR 0007：桌面界面与三语基线](adr/0007-frontend-style.md)

## 外部依据

外部文档于 2026-10-08 核对；接口权限和版本仍需实施时验证。

| 官方材料 | 使用范围 |
| --- | --- |
| [Tushare 数据目录](https://tushare.pro/document/2) | 数据集及证券标识参考 |
| [Tushare SDK/HTTP 调用](https://tushare.pro/document/1?doc_id=40) | 后端采集接入 |
| [Tushare 权限和频次](https://tushare.pro/document/2?doc_id=290) | 不假定 token 具备全部接口权限 |
| [OpenAI Python SDK](https://developers.openai.com/api/reference/python) | Responses 和客户端配置 |
| [Ant Design React](https://ant.design/docs/react/introduce/) | 组件和主题选型 |
| [FastAPI Docker 部署](https://fastapi.tiangolo.com/deployment/docker/) | 自建应用镜像和容器部署 |
| [PostgreSQL 行安全](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | 后续多用户的数据库防御层参考 |

来源可公开访问不等于授权批量采集或再分发。仓库不携带真实市场数据和新闻正文。

- [项目改名与历史兼容](adr/0009-project-name.md)。
