# XXStock Agent 角色模板与责任边界

状态：阶段 0 设计契约；角色目录描述未来职责，不表示业务 Agent、采集、回测或交易运行器已经实现。

每项任务绑定业务专责、实现责任和独立验收责任。实现者不能验收自己；所有模板均为 `mode=design`，`stage` 仅表示未来允许设计/启用的阶段。缺失保持缺失，冲突保留证据，阻断依赖不执行；盘前冻结稿保留原 snapshot_id/cutoff，盘后版本不能回填。

完整业务/工程池为 40 个，另有老板与 PM 两个协调角色，总计 42 个。

## 角色模板

### `data.source_ingestion`：数据源接入与采集

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：核对三家允许来源的权限、分页、频次、限流与失败重试，形成数据集采集边界。
- 必需输入：data.source_ingestion packet: 核对三家允许来源的权限、分页、频次、限流与失败重试，形成数据集采集边界。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：data.source_ingestion depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：数据源接入与采集的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：data.source_ingestion acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：data.source_ingestion cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：data.source_ingestion failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `data.standardization_quality`：数据标准化与质量

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：统一证券编码、交易日、单位、复权与板块成员版本，保证原始/标准化/计算层可追溯。
- 必需输入：data.standardization_quality packet: 统一证券编码、交易日、单位、复权与板块成员版本，保证原始/标准化/计算层可追溯。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：data.standardization_quality depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：数据标准化与质量的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：data.standardization_quality acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：data.standardization_quality cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：data.standardization_quality failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `data.historical_migration`：历史迁移

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：只读扫描旧资产，按来源血缘筛选，执行可断点、幂等、可回滚的分批导入。
- 必需输入：Legacy asset inventory, source lineage, migration allowlist, target schema, sample checks, checkpoints, and rollback fixtures.
- 前置依赖：Lineage admission, read-only legacy access, idempotency key, checkpoint protocol, rollback plan, and downstream refresh contract.
- 具体产物：历史迁移的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Every batch passes lineage admission and can resume from a checkpoint and roll back; migration must not break later refreshes or overwrite valid records.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot write the legacy database, start its scheduler, admit unknown lineage, or make the legacy path a runtime dependency.
- 缺失/冲突/失败交接：Handoff includes batch checkpoint, rollback point, isolation record, failed samples, and an assessment of later-update impact.

### `data.time_provenance`：数据与时间核验

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：核对来源链、首次可用时间、发布时间、修订和成员可得性，给出 point-in-time 范围。
- 必需输入：source_available_at, published_at, collected_at, cutoff, revision_id, member-effective dates, and missing-time fixtures.
- 前置依赖：Point-in-time policy, source clock calibration, cutoff policy, and revision handling must be approved before this role proceeds.
- 具体产物：数据与时间核验的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：If available_at is unknown or later than cutoff, keep the value missing and reject it from the snapshot; any revision is rejected or versioned with an evidence trail.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot substitute collected_at for available_at, use future information, erase a revision, or relax cutoff rules.
- 缺失/冲突/失败交接：Handoff includes each timestamp, cutoff decision, revision diff, rejection reason, and impacted report/experiment IDs.

### `market.structure_sentiment`：市场结构与情绪分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：计算指数、宽度、成交、涨跌分布、涨停结构和赚钱效应，声明范围与异常。
- 必需输入：market.structure_sentiment packet: 计算指数、宽度、成交、涨跌分布、涨停结构和赚钱效应，声明范围与异常。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.structure_sentiment depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：市场结构与情绪分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.structure_sentiment acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.structure_sentiment cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.structure_sentiment failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.sector_theme`：板块与题材分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按版本化成员分解行业/概念强弱、贡献、主线、龙头和轮动，禁止未来成员回填。
- 必需输入：market.sector_theme packet: 按版本化成员分解行业/概念强弱、贡献、主线、龙头和轮动，禁止未来成员回填。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.sector_theme depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：板块与题材分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.sector_theme acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.sector_theme cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.sector_theme failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.fund_flow_lhb`：资金流与龙虎榜分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：保留供应商资金定义和单位，分析连续变化、板块聚合和龙虎榜关联。
- 必需输入：market.fund_flow_lhb packet: 保留供应商资金定义和单位，分析连续变化、板块聚合和龙虎榜关联。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.fund_flow_lhb depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：资金流与龙虎榜分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.fund_flow_lhb acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.fund_flow_lhb cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.fund_flow_lhb failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.technical`：个股技术分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：在固定复权时序上计算趋势、支撑压力、波动和信号，明确触发与失效。
- 必需输入：market.technical packet: 在固定复权时序上计算趋势、支撑压力、波动和信号，明确触发与失效。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.technical depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：个股技术分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.technical acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.technical cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.technical failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.financial_valuation`：公司财务与估值分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按公告发布日期核对报表、盈利质量、现金流、负债、估值和同行可比性。
- 必需输入：market.financial_valuation packet: 按公告发布日期核对报表、盈利质量、现金流、负债、估值和同行可比性。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.financial_valuation depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：公司财务与估值分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.financial_valuation acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.financial_valuation cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.financial_valuation failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.news_event`：新闻电报与事件分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按发布时间归并新闻，维护主题、标的映射、确认状态、冲突和事件日历。
- 必需输入：market.news_event packet: 按发布时间归并新闻，维护主题、标的映射、确认状态、冲突和事件日历。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.news_event depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：新闻电报与事件分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.news_event acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.news_event cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.news_event failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.corporate_action`：公司公告与公司行动分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：记录公告、业绩预告、分红、增减持、解禁的发布日期、生效日期和修订版本。
- 必需输入：market.corporate_action packet: 记录公告、业绩预告、分红、增减持、解禁的发布日期、生效日期和修订版本。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.corporate_action depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：公司公告与公司行动分析的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.corporate_action acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.corporate_action cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.corporate_action failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `market.method_validation`：特色指标与方法验证

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：建立特色指标公式、样本、版本和限制，检验稳定性；未通过只能标实验。
- 必需输入：market.method_validation packet: 建立特色指标公式、样本、版本和限制，检验稳定性；未通过只能标实验。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：market.method_validation depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：特色指标与方法验证的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：market.method_validation acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：market.method_validation cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：market.method_validation failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `report.pre_open`：盘前策略

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：只用盘前截止快照生成情景、关注方向、观察条件和失效条件；冻结后不可回填。
- 必需输入：Prior close snapshot, 08:30 cutoff, 08:45 collection window, 08:50 freeze rule, and evidence snapshot.
- 前置依赖：Available-time checks, upstream market/event snapshots, prediction version, and freeze-state ledger.
- 具体产物：盘前策略的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Enforce 08:30 requirement cutoff, 08:45 collection, and 08:50 freeze; replay must reject information arriving after the freeze.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot read post-cutoff information, mutate frozen snapshot_id, or present a live conclusion as a frozen one.
- 缺失/冲突/失败交接：Handoff includes cutoff, collection batch, freeze snapshot, missing fields, unresolved dependencies, and prediction impact.

### `report.intraday`：盘中跟踪

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：以时间戳追加盘前条件触发、行情/事件变化和新增证据，不改写冻结稿。
- 必需输入：Intraday quotes, event deltas, available_at timestamps, prior report, and T-observation card.
- 前置依赖：Market clock, event deduplication, prior freeze, and adversarial review.
- 具体产物：盘中跟踪的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Every added fact has source and time; revisions are traceable; unconfirmed events never become facts.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot cross the time boundary, place orders, or treat AI interpretation as source fact.
- 缺失/冲突/失败交接：Handoff includes incremental evidence, before/after text, unconfirmed events, and conclusion impact.

### `report.post_close`：盘后复盘

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：用冻结稿、盘中记录和收盘证据解释差异，把事后因果保留为假设。
- 必需输入：Close snapshot, report versions, transaction-record references, anomaly log, and review range.
- 前置依赖：Close-time confirmation, data quality result, personal-asset ownership, and version linkage.
- 具体产物：盘后复盘的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Facts, explanations, suggestions, and personal records remain separate with complete citations and visible missing/conflict states.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot rewrite historical fills, fabricate uncollected facts, or turn a review suggestion into an executed order.
- 缺失/冲突/失败交接：Handoff includes close snapshot, citation gaps, version diff, review disputes, and open checks.

### `report.prediction_settlement`：预测结算与研究评估

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按版本化规则独立结算命中、失效或无法判定，不能改写原判断。
- 必需输入：08:50 frozen prediction, realized outcome, settlement window, sample labels, and unavailable markers.
- 前置依赖：Frozen version, point-in-time data, settlement clock, and historical evaluation sample.
- 具体产物：预测结算与研究评估的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Frozen predictions cannot be rewritten; outcomes settle only when available; unavailable outcomes remain missing and can be recalculated.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot use post-freeze information to rewrite a prediction or count unsettled samples in accuracy.
- 缺失/冲突/失败交接：Handoff includes freeze/settlement versions, unavailable outcomes, anomalous samples, metric changes, and recalculation conditions.

### `report.adversarial_review`：反方审查

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：逐项寻找替代解释、反证、时间穿越、样本偏差和遗漏风险，提出可复现意见。
- 必需输入：report.adversarial_review packet: 逐项寻找替代解释、反证、时间穿越、样本偏差和遗漏风险，提出可复现意见。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：report.adversarial_review depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：反方审查的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：report.adversarial_review acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：report.adversarial_review cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：report.adversarial_review failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `report.editorial_final`：报告审校与终稿复核

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：核对数字、引用、截止、事实/意见分层和反方处理，决定通过、退回或部分发布。
- 必需输入：report.editorial_final packet: 核对数字、引用、截止、事实/意见分层和反方处理，决定通过、退回或部分发布。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：report.editorial_final depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：报告审校与终稿复核的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：report.editorial_final acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：report.editorial_final cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：report.editorial_final failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `personal.research_management`：个人研究管理

- 分组 / 最低阶段 / 模式：`personal` / `2` / `design`
- 允许阶段范围：`2`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：维护用户股票池、自选、笔记、标签、收藏和上下文版本，手工资产不被自动内容覆盖。
- 必需输入：personal.research_management packet: 维护用户股票池、自选、笔记、标签、收藏和上下文版本，手工资产不被自动内容覆盖。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：personal.research_management depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：个人研究管理的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：personal.research_management acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：personal.research_management cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：personal.research_management failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `personal.monitor_alerts`：监控与提醒

- 分组 / 最低阶段 / 模式：`personal` / `2` / `design`
- 允许阶段范围：`2`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：定义价格、指标和事件提醒的触发、去重、确认、解除和失败状态，绑定用户与时间。
- 必需输入：personal.monitor_alerts packet: 定义价格、指标和事件提醒的触发、去重、确认、解除和失败状态，绑定用户与时间。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：personal.monitor_alerts depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：监控与提醒的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：personal.monitor_alerts acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：personal.monitor_alerts cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：personal.monitor_alerts failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `personal.trade_record_discipline`：交易记录与纪律复盘

- 分组 / 最低阶段 / 模式：`personal` / `2` / `design`
- 允许阶段范围：`2`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：解析核对私有成交记录，对照事前计划评估纪律偏差，解析与确认分离。
- 必需输入：personal.trade_record_discipline packet: 解析核对私有成交记录，对照事前计划评估纪律偏差，解析与确认分离。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：personal.trade_record_discipline depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：交易记录与纪律复盘的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：personal.trade_record_discipline acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：personal.trade_record_discipline cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：personal.trade_record_discipline failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `quant.strategy_research`：量化策略研究

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：提出可证伪因子/信号假设，冻结参数、基准、样本划分、费用口径和失效标准。
- 必需输入：Research hypothesis, factor definitions, point-in-time features, fees/slippage assumptions, program interface, engine interface, and experiment plan.
- 前置依赖：Frozen data lineage, program/engine API contracts, experiment registry, and a declared freeze policy are prerequisites.
- 具体产物：量化策略研究的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Hypothesis, data, program, engine versions, sample split, costs, and failed candidates are all frozen and reproducible before a conclusion is accepted.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot use future data, unregistered features, live credentials, or promote a research candidate to production.
- 缺失/冲突/失败交接：Handoff includes hypothesis, feature/version lock, sample range, failed candidates, cost assumptions, and blocked experiment dependencies.

### `quant.strategy_implementation`：量化程序开发

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：忠实实现冻结策略规格为确定性程序，固定参数、信号、持仓和行为测试。
- 必需输入：Strategy specification, program API, engine API, parameter schema, frozen data/program/engine version list, and synthetic market fixtures.
- 前置依赖：Research freeze, backend/worker interface, data-time semantics, deterministic runtime, and resource boundary.
- 具体产物：量化程序开发的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Program and engine interfaces are replayable; data, program, and engine versions are frozen; failed candidates and interface errors remain recorded.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot bypass unified data access, read secrets, or connect to broker/order interfaces.
- 缺失/冲突/失败交接：Handoff includes request/response contract, version lock, failed candidates, logs, and unmet interface clauses.

### `quant.backtest_engine`：回测引擎开发

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现时间推进、撮合、停牌/涨跌停、费用、滑点、收益核算和可重放对账。
- 必需输入：Trading calendar, adjusted prices, suspension/ST rules, fees, slippage, strategy version, and backtest parameters.
- 前置依赖：Strategy program/engine interface, point-in-time data, frozen experiment configuration, and deterministic seed.
- 具体产物：回测引擎开发的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Replay matches the frozen inputs and records fees, suspension, adjustment, calendar, anomalies, and failed candidates without survivor or look-ahead leakage.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot peek at future data, omit fees/slippage, use survivor-only samples, or rewrite a failed run.
- 缺失/冲突/失败交接：Handoff includes input snapshot, engine version, parameters, anomalous trades, failed candidates, and replay differences.

### `quant.experiment_execution`：回测实验执行

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：用冻结代码、数据和配置运行实验，保存交易明细、指标、资源状态和失败候选。
- 必需输入：Experiment registry, frozen data/program/engine versions, resource budget, metrics, and candidate strategies.
- 前置依赖：Strategy interfaces, backtest engine, experiment freeze policy, run ledger, and cost ceiling.
- 具体产物：回测实验执行的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：Each run is reproducible with complete version locks; failed candidates, runtime, and fee/resource consumption are retained.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot swap data or code mid-run, delete failures, exceed budget, or publish an unregistered result.
- 缺失/冲突/失败交接：Handoff includes run_id, version lock, logs, failed candidate, resource/fee usage, and replay conditions.

### `quant.independent_evaluation`：独立策略评估

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：独立复现实验，检查未来信息、幸存者偏差、参数选择、敏感性和样本外表现。
- 必需输入：Frozen experiment package, out-of-sample data, author/executor roster, evaluation plan, and leakage audit.
- 前置依赖：Independent evaluator assignment, experiment registry, out-of-sample split, leakage/survivorship/multiple-testing audit, and fee sensitivity plan.
- 具体产物：独立策略评估的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：This role is the evaluator: the evaluator must not be the strategy author or experiment executor; report out-of-sample performance, leakage, survivorship bias, multiple trials, and fee sensitivity.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：Cannot be the author or executor under review, alter frozen data, cherry-pick metrics, or access trading permissions.
- 缺失/冲突/失败交接：Handoff includes independence declaration, audit evidence, out-of-sample results, bias findings, fee sensitivity, and veto reasons.

### `quant.paper_trading_drift`：模拟交易与偏差监控

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：对比实时信号/模拟成交与回测，监控延迟、滑点、数据漂移和异常，不接触真实资金。
- 必需输入：quant.paper_trading_drift packet: 对比实时信号/模拟成交与回测，监控延迟、滑点、数据漂移和异常，不接触真实资金。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：quant.paper_trading_drift depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：模拟交易与偏差监控的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：quant.paper_trading_drift acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：quant.paper_trading_drift cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：quant.paper_trading_drift failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `quant.portfolio_risk`：投资组合与风险

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按独立规则检查仓位、集中度、相关暴露、流动性、损失限额和压力场景。
- 必需输入：quant.portfolio_risk packet: 按独立规则检查仓位、集中度、相关暴露、流动性、损失限额和压力场景。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：quant.portfolio_risk depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：投资组合与风险的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：quant.portfolio_risk acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：quant.portfolio_risk cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：quant.portfolio_risk failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `execution.order_engineering`：订单执行工程

- 分组 / 最低阶段 / 模式：`execution` / `5` / `design`
- 允许阶段范围：`5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：在另行授权下实现券商适配、幂等订单状态、成交对账、停止和恢复，动作可审计。
- 必需输入：execution.order_engineering packet: 在另行授权下实现券商适配、幂等订单状态、成交对账、停止和恢复，动作可审计。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：execution.order_engineering depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：订单执行工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：execution.order_engineering acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：execution.order_engineering cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：execution.order_engineering failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `execution.independent_risk`：独立执行风控

- 分组 / 最低阶段 / 模式：`execution` / `5` / `design`
- 允许阶段范围：`5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：独立核验资金、仓位、价格、时效、限额和停止开关，缺字段默认拒绝。
- 必需输入：execution.independent_risk packet: 独立核验资金、仓位、价格、时效、限额和停止开关，缺字段默认拒绝。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：execution.independent_risk depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：独立执行风控的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：execution.independent_risk acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：execution.independent_risk cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：execution.independent_risk failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `execution.strategy_operations`：策略运行与维护

- 分组 / 最低阶段 / 模式：`execution` / `5` / `design`
- 允许阶段范围：`5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：监测策略任务、数据漂移、退化和运行偏差，不静默改变批准策略或风控。
- 必需输入：execution.strategy_operations packet: 监测策略任务、数据漂移、退化和运行偏差，不静默改变批准策略或风控。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：execution.strategy_operations depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：策略运行与维护的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：execution.strategy_operations acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：execution.strategy_operations cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：execution.strategy_operations failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.architecture`：架构

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：维护模块边界、共享契约、阶段门槛、时间/权限决策和 ADR，阻止跨阶段集成。
- 必需输入：engineering.architecture packet: 维护模块边界、共享契约、阶段门槛、时间/权限决策和 ADR，阻止跨阶段集成。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.architecture depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：架构的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.architecture acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.architecture cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.architecture failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.frontend_interaction`：前端与交互

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现页面、图表、表单和移动布局，准确呈现缺失、过期、失败和归属状态。
- 必需输入：engineering.frontend_interaction packet: 实现页面、图表、表单和移动布局，准确呈现缺失、过期、失败和归属状态。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.frontend_interaction depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：前端与交互的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.frontend_interaction acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.frontend_interaction cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.frontend_interaction failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.backend_api`：后端 API

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现查询、领域服务、归属过滤和显式任务入口，普通读取不得隐式采集或调用 AI。
- 必需输入：engineering.backend_api packet: 实现查询、领域服务、归属过滤和显式任务入口，普通读取不得隐式采集或调用 AI。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.backend_api depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：后端 API的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.backend_api acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.backend_api cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.backend_api failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.database`：数据库工程

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：用显式迁移实现模型、revision、索引、归属约束、幂等发布和备份恢复。
- 必需输入：engineering.database packet: 用显式迁移实现模型、revision、索引、归属约束、幂等发布和备份恢复。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.database depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：数据库工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.database acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.database cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.database failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.worker`：作业与 worker 工程

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现任务依赖、原子领取、lease/fencing、重试、取消和恢复，过期 worker 不能写入。
- 必需输入：engineering.worker packet: 实现任务依赖、原子领取、lease/fencing、重试、取消和恢复，过期 worker 不能写入。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.worker depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：作业与 worker 工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.worker acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.worker cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.worker failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.ai_workflow`：AI 工作流工程

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：编排角色、白名单工具、证据引用、预算、结构化输出和运行审计。
- 必需输入：engineering.ai_workflow packet: 编排角色、白名单工具、证据引用、预算、结构化输出和运行审计。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.ai_workflow depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：AI 工作流工程的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.ai_workflow acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.ai_workflow cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.ai_workflow failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.qa_review`：独立 QA／代码审查

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：独立 forward-test 候选入口，复现边界、失败、权限、时间和回归问题，不能自验收。
- 必需输入：engineering.qa_review packet: 独立 forward-test 候选入口，复现边界、失败、权限、时间和回归问题，不能自验收。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.qa_review depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (pm); unresolved prerequisites keep the task in design.
- 具体产物：独立 QA／代码审查的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.qa_review acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`pm`
- 权限排除：engineering.qa_review cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.qa_review failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.security_ops`：安全与运维

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：管理秘密、隔离、脱敏日志、备份恢复、部署和通知故障，执行最小权限。
- 必需输入：engineering.security_ops packet: 管理秘密、隔离、脱敏日志、备份恢复、部署和通知故障，执行最小权限。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.security_ops depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：安全与运维的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.security_ops acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.security_ops cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.security_ops failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `engineering.integration_release`：集成与发布

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按发布锁合并，验证 exact SHA、版本、Actions、Release 和最终通知。
- 必需输入：engineering.integration_release packet: 按发布锁合并，验证 exact SHA、版本、Actions、Release 和最终通知。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：engineering.integration_release depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, pm); unresolved prerequisites keep the task in design.
- 具体产物：集成与发布的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：engineering.integration_release acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `pm`
- 权限排除：engineering.integration_release cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：engineering.integration_release failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `boss`：老板

- 分组 / 最低阶段 / 模式：`coordination` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：确认需求、阶段范围和发布授权，接收 PM 回执后释放对话。
- 必需输入：boss packet: 确认需求、阶段范围和发布授权，接收 PM 回执后释放对话。 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：boss depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (pm); unresolved prerequisites keep the task in design.
- 具体产物：老板的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：boss acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`pm`
- 权限排除：boss cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：boss failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

### `pm`：PM

- 分组 / 最低阶段 / 模式：`coordination` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：拆分业务专责、实现责任和独立验收，维护依赖、文件所有权、返工、集成、发布锁和汇报
- 必需输入：pm packet: 拆分业务专责、实现责任和独立验收，维护依赖、文件所有权、返工、集成、发布锁和汇报 Required evidence is role-scoped source data, synthetic fixtures, cutoff/as_of context, and version identifiers.
- 前置依赖：pm depends on its declared upstream data lineage, the unified access contract, stage gate, and reviewer set (engineering.qa_review, engineering.integration_release, boss); unresolved prerequisites keep the task in design.
- 具体产物：PM的结构化产物、来源/版本引用、缺口和失败状态。
- 验收条件：pm acceptance checks the role-specific responsibility, source/version trace, missing and conflict semantics, reproducibility, and explicit design-stage boundary.
- 指定复核：`engineering.qa_review`, `engineering.integration_release`, `boss`
- 权限排除：pm cannot read secrets, another user's assets, writable legacy modules, or live trading interfaces; it cannot invent missing inputs or grant permissions.
- 缺失/冲突/失败交接：pm failure handoff includes raw evidence references, version IDs, error class, affected outputs, blocking dependency, and the exact next review question; no empty-result substitution.

## 覆盖索引

下表与 `docs/development/agent-coverage.json` 的 `capabilities` 数组逐行对应；能力名称和行号直接取自 [功能审查与模块清单](../../../../docs/modules/catalog.md) 的实际 44 条能力行。

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

机器校验应检查：能力数 44；分组 data4/market8/report6/personal3/quant7/execution3/engineering9/coordination2；每角色契约字段非空；`stage` 为整数最低阶段，`stage_range` 保留细分范围；实现与验收集合不相交；角色引用存在；JSON 与本表顺序和三责一致。
