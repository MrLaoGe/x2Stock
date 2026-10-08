# XXStock Agent 角色模板与责任边界

状态：阶段 0 设计契约；角色目录描述未来职责，不表示业务 Agent、采集、回测或交易运行器已经实现。

每项任务绑定业务专责、实现责任和独立验收责任。实现者不能验收自己；所有模板均为 `mode=design`，`stage` 仅表示未来允许设计/启用的阶段。缺失保持缺失，冲突保留证据，阻断依赖不执行；盘前冻结稿保留原 snapshot_id/cutoff，盘后版本不能回填。

完整业务/工程池为 40 个，另有老板与 PM 两个协调角色，总计 42 个。

## 角色模板

### `data.source_ingestion`：数据源接入与采集

- 分组 / 阶段 / 模式：`data` / `1` / `design`
- 负责需求：负责数据源接入与采集的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：数据源接入与采集的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `data.standardization_quality`：数据标准化与质量

- 分组 / 阶段 / 模式：`data` / `1` / `design`
- 负责需求：负责数据标准化与质量的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：数据标准化与质量的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `data.historical_migration`：历史迁移

- 分组 / 阶段 / 模式：`data` / `1` / `design`
- 负责需求：负责历史迁移的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：历史迁移的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `data.time_provenance`：数据与时间核验

- 分组 / 阶段 / 模式：`data` / `1` / `design`
- 负责需求：负责数据与时间核验的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：数据与时间核验的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.structure_sentiment`：市场结构与情绪分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责市场结构与情绪分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：市场结构与情绪分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.sector_theme`：板块与题材分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责板块与题材分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：板块与题材分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.fund_flow_lhb`：资金流与龙虎榜分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责资金流与龙虎榜分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：资金流与龙虎榜分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.technical`：个股技术分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责个股技术分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：个股技术分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.financial_valuation`：公司财务与估值分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责公司财务与估值分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：公司财务与估值分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.news_event`：新闻电报与事件分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责新闻电报与事件分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：新闻电报与事件分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.corporate_action`：公司公告与公司行动分析

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责公司公告与公司行动分析的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：公司公告与公司行动分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `market.method_validation`：特色指标与方法验证

- 分组 / 阶段 / 模式：`market` / `2/3` / `design`
- 负责需求：负责特色指标与方法验证的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：特色指标与方法验证的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `report.pre_open`：盘前策略

- 分组 / 阶段 / 模式：`report` / `3` / `design`
- 负责需求：负责盘前策略的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：盘前策略的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `report.intraday`：盘中跟踪

- 分组 / 阶段 / 模式：`report` / `3` / `design`
- 负责需求：负责盘中跟踪的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：盘中跟踪的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `report.post_close`：盘后复盘

- 分组 / 阶段 / 模式：`report` / `3` / `design`
- 负责需求：负责盘后复盘的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：盘后复盘的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `report.prediction_settlement`：预测结算与研究评估

- 分组 / 阶段 / 模式：`report` / `3` / `design`
- 负责需求：负责预测结算与研究评估的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：预测结算与研究评估的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `report.adversarial_review`：反方审查

- 分组 / 阶段 / 模式：`report` / `3` / `design`
- 负责需求：负责反方审查的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：反方审查的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `report.editorial_final`：报告审校与终稿复核

- 分组 / 阶段 / 模式：`report` / `3` / `design`
- 负责需求：负责报告审校与终稿复核的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：报告审校与终稿复核的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `personal.research_management`：个人研究管理

- 分组 / 阶段 / 模式：`personal` / `2` / `design`
- 负责需求：负责个人研究管理的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：个人研究管理的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `personal.monitor_alerts`：监控与提醒

- 分组 / 阶段 / 模式：`personal` / `2` / `design`
- 负责需求：负责监控与提醒的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：监控与提醒的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `personal.trade_record_discipline`：交易记录与纪律复盘

- 分组 / 阶段 / 模式：`personal` / `2` / `design`
- 负责需求：负责交易记录与纪律复盘的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：交易记录与纪律复盘的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.strategy_research`：量化策略研究

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责量化策略研究的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：量化策略研究的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.strategy_implementation`：量化程序开发

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责量化程序开发的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：量化程序开发的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.backtest_engine`：回测引擎开发

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责回测引擎开发的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：回测引擎开发的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.experiment_execution`：回测实验执行

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责回测实验执行的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：回测实验执行的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.independent_evaluation`：独立策略评估

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责独立策略评估的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：独立策略评估的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.paper_trading_drift`：模拟交易与偏差监控

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责模拟交易与偏差监控的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：模拟交易与偏差监控的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `quant.portfolio_risk`：投资组合与风险

- 分组 / 阶段 / 模式：`quant` / `4` / `design`
- 负责需求：负责投资组合与风险的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：投资组合与风险的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `execution.order_engineering`：订单执行工程

- 分组 / 阶段 / 模式：`execution` / `5` / `design`
- 负责需求：负责订单执行工程的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：订单执行工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `execution.independent_risk`：独立执行风控

- 分组 / 阶段 / 模式：`execution` / `5` / `design`
- 负责需求：负责独立执行风控的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：独立执行风控的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `execution.strategy_operations`：策略运行与维护

- 分组 / 阶段 / 模式：`execution` / `5` / `design`
- 负责需求：负责策略运行与维护的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：策略运行与维护的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.architecture`：架构

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责架构的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：架构的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.frontend_interaction`：前端与交互

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责前端与交互的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：前端与交互的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.backend_api`：后端 API

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责后端 API的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：后端 API的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.database`：数据库工程

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责数据库工程的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：数据库工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.worker`：作业与 worker 工程

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责作业与 worker 工程的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：作业与 worker 工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.ai_workflow`：AI 工作流工程

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责AI 工作流工程的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：AI 工作流工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.qa_review`：独立 QA／代码审查

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责独立 QA／代码审查的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：独立 QA／代码审查的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.security_ops`：安全与运维

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责安全与运维的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：安全与运维的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `engineering.integration_release`：集成与发布

- 分组 / 阶段 / 模式：`engineering` / `0-5` / `design`
- 负责需求：负责集成与发布的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：集成与发布的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `boss`：老板

- 分组 / 阶段 / 模式：`coordination` / `0-5` / `design`
- 负责需求：负责老板的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：老板的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`pm`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

### `pm`：PM

- 分组 / 阶段 / 模式：`coordination` / `0-5` / `design`
- 负责需求：负责PM的业务规则、范围和阶段性产物。
- 必需输入：批准方案、相关模块契约、合成或已授权证据、任务截止与版本上下文。
- 前置依赖：依赖对应阶段门槛、数据/权限边界和 PM 已接受的前置任务；无前置时使用已接受需求与合成输入。
- 具体产物：PM的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：产物可追溯、可复核、保留缺失与冲突，且不超出 design 模式和阶段边界。
- 指定复核：`engineering.qa_review`, `engineering.integration_release`, `boss`
- 权限排除：不得越权读取秘密、其他用户资产、旧项目或交易接口；不得把设计契约冒充已运行能力。
- 缺失/冲突/失败交接：保留原始证据、候选版本、错误和影响范围，向 PM 交接；阻断依赖不执行，不以空结果补齐。

## 覆盖索引

下表与 `docs/development/agent-coverage.json` 的 `capabilities` 数组逐行对应；能力名称和行号直接取自 [功能审查与模块清单](../../../docs/modules/catalog.md) 的实际 43 条能力行。

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
| 9 | 板块资金流、个股资金和历史轨迹 | `market.sector_theme` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `engineering.qa_review` |
| 10 | 热力图、历史日期与盘中回放 | `market.structure_sentiment` | `engineering.backend_api`, `engineering.frontend_interaction` | `data.time_provenance`, `engineering.qa_review` |
| 11 | 新闻电报、公告、同步与时间线 | `market.news_event`, `market.corporate_action` | `engineering.backend_api`, `engineering.worker` | `data.time_provenance`, `engineering.qa_review` |
| 12 | 新闻主题、股票/板块映射与关联 | `market.news_event` | `engineering.backend_api`, `engineering.ai_workflow` | `report.adversarial_review`, `engineering.qa_review` |
| 13 | 新闻详情、收藏/已读与规则评分 | `market.news_event`, `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 14 | 单条新闻 AI 解读 | `market.news_event` | `engineering.ai_workflow`, `engineering.backend_api` | `report.adversarial_review`, `engineering.qa_review` |
| 15 | 未来大事件、消息/流言与结束状态 | `market.news_event`, `market.corporate_action` | `engineering.backend_api`, `engineering.worker` | `data.time_provenance`, `report.adversarial_review` |
| 16 | 股票搜索、股票池和名单配置 | `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 17 | 个人研究笔记、标签与上下文 | `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 18 | 实时/日 K/分钟行情和个股资料 | `market.technical` | `data.source_ingestion`, `engineering.backend_api` | `data.time_provenance`, `engineering.qa_review` |
| 19 | 压力/支撑监控、阈值与提醒确认 | `personal.monitor_alerts` | `engineering.backend_api`, `engineering.worker`, `engineering.frontend_interaction` | `engineering.qa_review`, `engineering.security_ops` |
| 20 | 对子数价格提醒及特殊观察规则 | `personal.monitor_alerts`, `market.technical` | `engineering.backend_api`, `engineering.worker` | `market.method_validation`, `engineering.qa_review` |
| 21 | 个股分析、技术筛选与选股实验 | `market.technical` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `engineering.qa_review` |
| 22 | 龙虎榜、公告与个股消息证据 | `market.fund_flow_lhb`, `market.corporate_action`, `market.news_event` | `engineering.backend_api` | `data.time_provenance`, `engineering.qa_review` |
| 23 | 情绪时间线、趋势阶段和情绪板 | `market.structure_sentiment`, `market.method_validation` | `engineering.backend_api`, `engineering.frontend_interaction` | `data.time_provenance`, `engineering.qa_review` |
| 24 | 风险/机遇指数及模型建议仓位 | `market.method_validation` | `engineering.backend_api`, `engineering.ai_workflow` | `report.adversarial_review`, `quant.independent_evaluation` |
| 25 | 本金/融资仓位和用户持仓口径 | `personal.research_management` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 26 | 今日/月度平均收益参考线 | `market.method_validation` | `engineering.backend_api` | `report.adversarial_review`, `engineering.qa_review` |
| 27 | 赚钱/亏钱效应与市场结构指标 | `market.structure_sentiment` | `engineering.backend_api` | `market.method_validation`, `engineering.qa_review` |
| 28 | 拥挤度、大盘/板块/个股观察列表 | `market.structure_sentiment`, `market.technical` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `data.time_provenance` |
| 29 | 题材主线、强弱领导和轮动日历 | `market.sector_theme` | `engineering.backend_api`, `engineering.frontend_interaction` | `market.method_validation`, `data.time_provenance` |
| 30 | 宝妈指数等社区情绪实验 | `market.method_validation` | `engineering.worker`, `engineering.ai_workflow` | `report.adversarial_review`, `engineering.qa_review` |
| 31 | 盘前/盘中/盘后策略报告 | `report.pre_open`, `report.intraday`, `report.post_close` | `engineering.ai_workflow`, `engineering.backend_api`, `engineering.frontend_interaction` | `report.adversarial_review`, `report.editorial_final` |
| 32 | 08:50 盘前预测冻结与结算 | `report.pre_open`, `report.prediction_settlement` | `engineering.worker`, `engineering.ai_workflow` | `data.time_provenance`, `report.editorial_final` |
| 33 | 交易模型文档和个人方法资产 | `report.editorial_final`, `personal.research_management` | `engineering.backend_api` | `engineering.qa_review`, `engineering.security_ops` |
| 34 | 日内 T 观察、动作卡片与纪律规则 | `report.intraday`, `personal.monitor_alerts` | `engineering.backend_api`, `engineering.frontend_interaction` | `report.adversarial_review`, `engineering.qa_review` |
| 35 | 交易记录与文本导入、复盘关联 | `personal.trade_record_discipline` | `engineering.backend_api`, `engineering.frontend_interaction` | `engineering.security_ops`, `engineering.qa_review` |
| 36 | 提醒通知、已确认状态 | `personal.monitor_alerts` | `engineering.worker`, `engineering.backend_api` | `engineering.qa_review`, `engineering.security_ops` |
| 37 | 桌面通知、外部消息推送 | `personal.monitor_alerts` | `engineering.worker`, `engineering.security_ops` | `engineering.qa_review`, `engineering.architecture` |
| 38 | Skill 蓝图、文档注册与依赖治理 | `pm` | `engineering.architecture`, `engineering.integration_release` | `engineering.qa_review`, `engineering.security_ops` |
| 39 | 项目 Skill 目录与注册表 | `engineering.architecture` | `engineering.integration_release` | `engineering.qa_review`, `engineering.security_ops` |
| 40 | 正式版本、标签、Release 与最终通知 | `pm` | `engineering.integration_release`, `engineering.security_ops` | `engineering.qa_review`, `boss` |
| 41 | 多 Agent 研究、审校与报告记录 | `report.adversarial_review`, `report.editorial_final` | `engineering.ai_workflow`, `engineering.backend_api` | `engineering.qa_review`, `data.time_provenance` |
| 42 | 量化因子、回测与模拟交易 | `quant.strategy_research`, `quant.strategy_implementation`, `quant.backtest_engine`, `quant.experiment_execution`, `quant.independent_evaluation`, `quant.paper_trading_drift`, `quant.portfolio_risk` | `engineering.worker`, `engineering.database`, `engineering.ai_workflow` | `quant.independent_evaluation`, `engineering.qa_review` |
| 43 | 真实订单执行与长期策略维护 | `execution.order_engineering`, `execution.independent_risk`, `execution.strategy_operations` | `engineering.backend_api`, `engineering.worker`, `engineering.security_ops` | `engineering.qa_review`, `engineering.architecture` |

机器校验应检查：能力数 43；分组 data4/market8/report6/personal3/quant7/execution3/engineering9/coordination2；每角色九个契约字段非空；实现与验收集合不相交；角色引用存在；JSON 与本表顺序和三责一致。

