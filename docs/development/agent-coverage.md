# Agent 模块责任覆盖

状态：阶段 0 设计契约。此表用于派单和独立验收，不代表业务页面、采集服务、量化引擎或交易接口已经实现。

每项能力固定三责：业务专责定义研究/产品口径，实现责任落实工程边界，独立验收从需求和候选入口复核。实现责任与独立验收不得由同一角色承担。`stage` 是脚本可读取的最低执行阶段，JSON 中的 `stage_range` 保留细分范围；所有角色的 `mode` 为 `design`，实际启用仍须经过阶段门和独立审查。

目录来源为 [功能审查与模块清单](../modules/catalog.md)，当前实际 44 条能力；早期“43 条”是计数错误，第 9 条行业/概念指数、自选板块已纳入。机器契约见 [agent-coverage.json](agent-coverage.json)，角色全文见 [roles.md](../../.agents/skills/multi-dialogue-development/references/roles.md)。

## 覆盖表

| 行 | 能力 | 业务专责 | 实现责任 | 独立验收 |
| ---: | --- | --- | --- | --- |
| 1 | 来源配置、能力和权限核验 | `data.source_ingestion` | `engineering.backend_api`, `engineering.security_ops` | `data.time_provenance`, `engineering.qa_review` |
| 2 | 标准化事实、原始引用、字段质量 | `data.standardization_quality` | `engineering.database`, `engineering.backend_api` | `data.time_provenance`, `engineering.qa_review` |
| 3 | 来源探测、覆盖率与可用性审计 | `data.source_ingestion` | `engineering.backend_api`, `engineering.worker` | `data.time_provenance`, `engineering.qa_review` |
| 4 | 历史导入、预检、隔离和补缺 | `data.historical_migration` | `engineering.database`, `engineering.worker` | `data.time_provenance`, `engineering.qa_review` |
| 5 | 刷新、自动任务、依赖、手动运行 | `data.source_ingestion` | `engineering.worker`, `engineering.backend_api` | `engineering.qa_review`, `engineering.security_ops` |
| 6 | 健康检查、日志、备份恢复 | `data.time_provenance` | `engineering.security_ops`, `engineering.database` | `engineering.qa_review`, `engineering.architecture` |
| 7 | 首页摘要、指数与全球参考 | `market.structure_sentiment` | `engineering.backend_api`, `engineering.frontend_interaction` | `data.time_provenance`, `engineering.qa_review` |
| 8 | 市场宽度、成交额、涨跌分布 | `market.structure_sentiment` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `engineering.qa_review` |
| 9 | 行业/概念指数、自选板块 | `market.sector_theme` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `data.time_provenance` |
| 10 | 板块资金流、个股资金和历史轨迹 | `market.sector_theme` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `engineering.qa_review` |
| 11 | 热力图、历史日期与盘中回放 | `market.structure_sentiment` | `engineering.backend_api`, `engineering.frontend_interaction` | `data.time_provenance`, `engineering.qa_review` |
| 12 | 新闻电报、公告、同步与时间线 | `market.news_event`, `market.corporate_action` | `engineering.backend_api`, `engineering.worker` | `data.time_provenance`, `engineering.qa_review` |
| 13 | 新闻主题、股票/板块映射与关联 | `market.news_event` | `engineering.backend_api`, `engineering.ai_workflow` | `report.adversarial_review`, `engineering.qa_review` |
| 14 | 新闻详情、收藏/已读与规则评分 | `market.news_event`, `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 15 | 单条新闻 AI 解读 | `market.news_event` | `engineering.ai_workflow`, `engineering.backend_api` | `report.adversarial_review`, `engineering.qa_review` |
| 16 | 未来大事件、消息/流言与结束状态 | `market.news_event`, `market.corporate_action` | `engineering.backend_api`, `engineering.worker` | `data.time_provenance`, `report.adversarial_review` |
| 17 | 股票搜索、股票池和名单配置 | `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 18 | 个人研究笔记、标签与上下文 | `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 19 | 实时/日 K/分钟行情和个股资料 | `market.technical` | `data.source_ingestion`, `engineering.backend_api` | `data.time_provenance`, `engineering.qa_review` |
| 20 | 压力/支撑监控、阈值与提醒确认 | `personal.monitor_alerts` | `engineering.backend_api`, `engineering.worker`, `engineering.frontend_interaction` | `engineering.qa_review`, `engineering.security_ops` |
| 21 | 对子数价格提醒及特殊观察规则 | `personal.monitor_alerts`, `market.technical` | `engineering.backend_api`, `engineering.worker` | `market.method_validation`, `engineering.qa_review` |
| 22 | 个股分析、技术筛选与选股实验 | `market.technical` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `engineering.qa_review` |
| 23 | 龙虎榜、公告与个股消息证据 | `market.fund_flow_lhb`, `market.corporate_action`, `market.news_event` | `engineering.backend_api` | `data.time_provenance`, `engineering.qa_review` |
| 24 | 情绪时间线、趋势阶段和情绪板 | `market.structure_sentiment`, `market.method_validation` | `engineering.backend_api`, `engineering.frontend_interaction` | `data.time_provenance`, `engineering.qa_review` |
| 25 | 风险/机遇指数及模型建议仓位 | `market.method_validation` | `engineering.backend_api`, `engineering.ai_workflow` | `report.adversarial_review`, `quant.independent_evaluation` |
| 26 | 本金/融资仓位和用户持仓口径 | `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 27 | 今日/月度平均收益参考线 | `market.method_validation` | `engineering.backend_api` | `report.adversarial_review`, `engineering.qa_review` |
| 28 | 赚钱/亏钱效应与市场结构指标 | `market.structure_sentiment` | `engineering.backend_api` | `market.method_validation`, `engineering.qa_review` |
| 29 | 拥挤度、大盘/板块/个股观察列表 | `market.structure_sentiment`, `market.technical` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `data.time_provenance` |
| 30 | 题材主线、强弱领导和轮动日历 | `market.sector_theme` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `data.time_provenance` |
| 31 | 宝妈指数等社区情绪实验 | `market.method_validation` | `engineering.worker`, `engineering.ai_workflow` | `report.adversarial_review`, `engineering.qa_review` |
| 32 | 盘前/盘中/盘后策略报告 | `report.pre_open`, `report.intraday`, `report.post_close` | `engineering.ai_workflow`, `engineering.backend_api`, `engineering.frontend_interaction` | `report.adversarial_review`, `report.editorial_final` |
| 33 | 08:50 盘前预测冻结与结算 | `report.pre_open`, `report.prediction_settlement` | `engineering.worker`, `engineering.ai_workflow` | `data.time_provenance`, `report.editorial_final` |
| 34 | 交易模型文档和个人方法资产 | `report.editorial_final`, `personal.research_management` | `engineering.backend_api` | `engineering.qa_review`, `engineering.security_ops` |
| 35 | 日内 T 观察、动作卡片与纪律规则 | `report.intraday`, `personal.monitor_alerts` | `engineering.backend_api`, `engineering.frontend_interaction` | `report.adversarial_review`, `engineering.qa_review` |
| 36 | 交易记录与文本导入、复盘关联 | `personal.trade_record_discipline` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 37 | 提醒通知、已确认状态 | `personal.monitor_alerts` | `engineering.worker`, `engineering.backend_api` | `engineering.qa_review`, `engineering.security_ops` |
| 38 | 桌面通知、外部消息推送 | `personal.monitor_alerts` | `engineering.worker`, `engineering.security_ops` | `engineering.qa_review`, `engineering.architecture` |
| 39 | Skill 蓝图、文档注册与依赖治理 | `pm` | `engineering.architecture`, `engineering.integration_release` | `engineering.qa_review`, `engineering.security_ops` |
| 40 | 项目 Skill 目录与注册表 | `engineering.architecture` | `engineering.integration_release` | `engineering.qa_review`, `engineering.security_ops` |
| 41 | 正式版本、标签、Release 与最终通知 | `pm` | `engineering.integration_release`, `engineering.security_ops` | `engineering.qa_review`, `boss` |
| 42 | 多 Agent 研究、审校与报告记录 | `report.adversarial_review`, `report.editorial_final` | `engineering.ai_workflow`, `engineering.backend_api` | `engineering.qa_review`, `data.time_provenance` |
| 43 | 量化因子、回测与模拟交易 | `quant.strategy_research`, `quant.strategy_implementation`, `quant.backtest_engine`, `quant.experiment_execution`, `quant.independent_evaluation`, `quant.paper_trading_drift`, `quant.portfolio_risk` | `engineering.worker`, `engineering.database`, `engineering.ai_workflow` | `quant.independent_evaluation`, `engineering.qa_review` |
| 44 | 真实订单执行与长期策略维护 | `execution.order_engineering`, `execution.independent_risk`, `execution.strategy_operations` | `engineering.backend_api`, `engineering.worker`, `engineering.security_ops` | `engineering.qa_review`, `engineering.architecture` |

## 角色分组与派单约束

- 数据 4、市场 8、报告 6、个人研究 3、量化 7、执行 3、工程 9、协调 2，共 42 个角色。
- 数据时间核验必须处理 `available_at` 未知、晚于 `cutoff` 和修订拒绝；历史迁移必须通过血缘准入、断点和回滚，并保证不破坏后续更新。
- 量化派单必须锁定程序/引擎接口、数据/程序/引擎版本、失败候选，并由独立评估角色覆盖样本外、泄露、幸存者、多试验和费用敏感性。
- 报告派单必须保留 08:30 消息截止；08:40 发布或 08:45 采集的消息不得进入 08:30 消息范围；完成 08:45 采集后于 08:50 冻结；无正式快照时标记无法回放。
- 失败交接保留证据、版本、影响范围、阻断依赖和下一步验收问题；不得以空结果覆盖有效数据。
