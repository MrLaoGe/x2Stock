# 任务台账

更新时间：2026-10-08。阶段 0 文档状态与远端发布状态分开记录。

| ID | 任务 | 负责人角色 | 状态 | 产物 / 下一步 |
| --- | --- | --- | --- | --- |
| S0-001 | 旧功能、架构和存储只读审计 | 架构 / 数据 Agent | completed | 旧审计、功能清单；未修改旧项目 |
| S0-002 | 确认目标、许可、来源、部署和首模块 | 主 Agent / 用户 | completed | 总体方案与 ADR |
| S0-003 | 新文档仓库、规范和配置模板 | 主 Agent | completed | README、AGENTS、设计、台账和校验 |
| S0-004 | 数据来源与历史迁移设计 | 数据 Agent | completed | 来源矩阵、审计、迁移、数据模块 |
| S0-005 | 架构、契约、界面与功能归并 | 架构 Agent | completed | 架构、接口、UI、模块目录 |
| S0-006 | 独立评审与公开资产验证 | 审查 / 主 Agent | completed | 32 公开资产校验；CI差异与worker领取代次问题已修正 |
| S0-007 | 创建并发布 MrLaoGe/XXStock | 主 Agent | completed | [公开仓库](https://github.com/MrLaoGe/XXStock)，MIT；初次远端main提交和32文件与本地一致 |
| S0-008 | Git push 自动通知 VChat #19 | 主 Agent / 审查 | completed | 23测试与独立审查通过；实际push触发[通知](https://github.com/MrLaoGe/XXStock/actions/runs/37757570650)，频道19返回HTTP200 |
| S0-009 | 项目 Skill 标准化与正式版本发布 | 主 Agent / 文档 / 审查 | in_progress | 本地实现与独立审查完成，43测试、51公开资产、Skill及版本校验通过；0.1.0远端Release与最终通知待本次工作流，结果保留于Actions及对话 |
| S0-011 | 独立新建与按模块复用路线调整 | 独立 PM / 独立审查 | in_progress | ADR 0006、当前入口与迁移规则统一；本地候选待独立审查，等待 S0-010 发布后集成；[交接](handoffs/module-first-roadmap.md) |
| S1-001 | 最小应用骨架 | 后续对话 | planned | 独立前后端/PG、显式结构升级、配置健康、空工作台与部署；仅规划未实现 |

## 下一轮入口

下一项本体任务为[最小应用骨架](../modules/application-skeleton.md)，当前仅规划，未实现数据库、采集、迁移、API、业务页面、产品 Agent、回测或交易执行。骨架无需旧项目/来源凭据/AI，结构升级与旧数据导入分开。其后业务模块由用户逐个选择，无固定队列；默认不迁移旧数据，评估不等于执行授权，未选模块不建业务表、不部署采集/导入任务。

数据中心随已启用模块增长。每模块分别记录功能、数据取得、迁移状态；新采集满足需求即可上线，不等待可选迁移。旧 S0-001 至 S0-004 为历史盘点/设计完成，不表示旧数据已导入或当前首模块已选。路线决定见 [ADR 0006](../adr/0006-module-first-new-project.md)。

## 路线调整（S0-011）

本轮只交付文档；本地验证、独立审查与外部发布分别验收。与 S0-010 Skill 任务并行准备，先等其 Git、Release、Actions、#19 通知全部验收，再集成最新 main 并计算实际下一 patch；未提前占用版本。角色模板、协调脚本、行为测试和发布流水线不属本轮修改范围，前任务成果须完整保留。旧项目和真实业务数据未修改。当前审查/验证进度见[本轮交接](handoffs/module-first-roadmap.md)。

## 本轮验证

- `python scripts/verify_repository.py`：通过，32 个公开资产；相对文件链接、UTF-8、JSON、配置一致性与常见凭据模式。
- `git diff --check`：通过；另在隔离临时 Git 仓库验证提交差异和首次提交空树检查能拒绝尾随空格，干净修复通过。
- 校验函数的 12 项行为核验：空秘密、密钥模式、秘密赋值、带 token URL、带密码 URI、正常/缺失/越界/绝对路径链接、代码块与配置准入。
- 独立审查：原两项问题已修正并定向复核，无剩余阻断问题；worker执行与数据库回滚是未来代码验收，未在本轮运行。
- 旧项目 Git 状态与开始时一致，本轮未修改旧项目或导入业务数据。来源数量是旧系统审计快照，不构成新版接口权限实测。
- 全新 GitHub 克隆：无需旧项目、业务运行依赖或用户凭据，公开资产校验通过，工作区干净。
- 首次 [GitHub Actions](https://github.com/MrLaoGe/XXStock/actions/runs/37754656719) 通过；发布交接记录的后续提交继续由同一流水线验证，最新结果见仓库 Actions。

## Skill 与正式发布（S0-009）

本轮 Skill、登记、版本 helper、说明、工作流和规范已在本地完成。43 项合成测试、51 个公开资产校验、Skill frontmatter 与引用、版本材料及差异检查通过；独立审查已复核历史材料不可改写、非快进主线拒绝发布、精确标签路由与 UTF-8。尚未据此验收 `0.1.0` GitHub Release 或本批 #19 最终通知，等待本次推送后的工作流。正式发布结果在 Actions 与用户输出中报告，不为写成功记录追加发布提交。见 [交接](handoffs/skill-releases.md)。

## Git 通知验收（S0-008，历史记录）

- 已配置 GitHub Secrets（地址/密钥）和 Variables（启用、频道19、前缀、超时），本机秘密仅在被忽略的 `.env`；3.0配置未修改。
- 23合成测试、公开资产校验和独立审查通过；HTTP协议异常泄露原文的问题已修复并验证。
- 功能提交的真实push触发通知；[专用工作流](https://github.com/MrLaoGe/XXStock/actions/runs/37757570650)记录 `sent`、频道19、HTTP200。
- 同次[开发校验](https://github.com/MrLaoGe/XXStock/actions/runs/37757570653)通过。通知成功与开发校验分别记录；本轮 S0-009 将正式 main 改为同一发布工作流最终通知，其他 push 的行为见当前通知规范。
- 配置、限制和失败处理见[通知说明](git-notifications.md)，本轮交接见[通知交接](handoffs/git-notifications.md)。
