# XXStock Agent 角色模板与责任边界

状态：阶段 0 设计契约；角色目录描述未来职责，不表示业务 Agent、采集、回测或交易运行器已经实现。

每项任务绑定业务专责、实现责任和独立验收责任。实现者不能验收自己；所有模板均为 `mode=design`，`stage` 仅表示未来允许设计/启用的阶段。缺失保持缺失，冲突保留证据，阻断依赖不执行；盘前冻结稿保留原 snapshot_id/cutoff，盘后版本不能回填。

完整业务/工程池为 40 个，另有老板与 PM 两个协调角色，总计 42 个。

## 角色模板

<a id="data-source-ingestion"></a>
### `data.source_ingestion`：数据源接入与采集

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：核对三家允许来源的权限、分页、频次、限流与失败重试，形成数据集采集边界。
- 必需输入：已核验的 Tushare、东方财富、财联社数据集清单；权限、频率、分页和限流契约；合成成功/429/解析失败响应。
- 前置依赖：依赖准入来源清单、各 provider adapter 契约、任务调度窗口和脱敏日志规则；未通过能力核验不得派采集。
- 具体产物：来源能力矩阵、字段覆盖表、分页 checkpoint、重试状态映射和失败分类表。
- 验收条件：429 只按有限退避重试；解析失败不得覆盖已有有效记录；分页游标完整闭合；日志和产物不输出 token。
- 指定复核：`data.time_provenance`, `engineering.qa_review`
- 权限排除：不得调用排除来源、读取/打印 token、绕过 adapter 直连 provider 或写旧库。
- 缺失/冲突/失败交接：交给 PM 与 data.standardization_quality；附来源、窗口、游标、状态码、失败响应和受影响字段。

<a id="data-standardization-quality"></a>
### `data.standardization_quality`：数据标准化与质量

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：统一证券编码、交易日、单位、复权与板块成员版本，保证原始/标准化/计算层可追溯。
- 必需输入：原始 provider 响应、字段字典、证券编码映射、交易日历、单位/时区/复权规则和来源引用。
- 前置依赖：依赖 data.source_ingestion 的能力矩阵与原始快照，依赖 data.time_provenance 的可得时间判断；冲突字段先隔离。
- 具体产物：标准证券事实表、字段转换清单、原始引用链、质量标记和缺失/冲突报告。
- 验收条件：原始层只读且可回放；转换幂等；单位、时区、复权和编码可重算；缺失保持缺失，不能用空值覆盖有效记录。
- 指定复核：`data.time_provenance`, `engineering.database`, `engineering.qa_review`
- 权限排除：不得改原始层、静默舍入金额、以采集时间代替发布时间或替用户资产补字段。
- 缺失/冲突/失败交接：交给 data.source_ingestion 与 data.time_provenance；附原始字段、转换前后值、版本和冲突样本。

<a id="data-historical-migration"></a>
### `data.historical_migration`：历史迁移

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：只读扫描旧资产，按来源血缘筛选，执行可断点、幂等、可回滚的分批导入。
- 必需输入：旧资产清单、来源血缘、允许迁移范围、目标 schema、样本校验、批次 checkpoint、备份和 rollback fixture。
- 前置依赖：依赖旧项目只读挂载、血缘准入规则、显式 Alembic 迁移、幂等键、备份恢复方案和后续刷新契约。
- 具体产物：血缘准入清单、分批迁移计划、checkpoint/rollback 记录、隔离区结果和后续更新兼容报告。
- 验收条件：每批都能断点续跑和回滚；不明血缘拒绝；迁移不得破坏后续刷新、重复写入或覆盖已有有效记录。
- 指定复核：`data.time_provenance`, `engineering.database`, `engineering.qa_review`
- 权限排除：不得写旧数据库、启动旧调度器、放行不明血缘或将旧路径作为新版依赖。
- 缺失/冲突/失败交接：交给 PM、engineering.database 与 data.source_ingestion；附批次、checkpoint、回滚点、失败样本和后续刷新影响。

<a id="data-time-provenance"></a>
### `data.time_provenance`：数据与时间核验

- 分组 / 最低阶段 / 模式：`data` / `1` / `design`
- 允许阶段范围：`1`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：核对来源链、首次可用时间、发布时间、修订和成员可得性，给出 point-in-time 范围。
- 必需输入：source_available_at、published_at、collected_at、cutoff、revision_id、成员生效区间和未知时间样本。
- 前置依赖：依赖原始引用、来源时钟校准、point-in-time 规则、截止策略和修订政策；时间不明时阻断下游。
- 具体产物：时间血缘账本、cutoff 判定、修订链、拒绝原因表和受影响快照清单。
- 验收条件：available_at 未知或晚于 cutoff 时保持缺失并拒绝纳入；发生修订时保留旧版本和差异，禁止未来信息回填。
- 指定复核：`data.standardization_quality`, `engineering.qa_review`
- 权限排除：不得以 collected_at 冒充 available_at、回填未来信息、删除修订痕迹或放宽 cutoff。
- 缺失/冲突/失败交接：交给 PM、report.prediction_settlement 与 quant.independent_evaluation；附时间戳、cutoff 判定、修订差异和拒绝原因。

<a id="market-structure-sentiment"></a>
### `market.structure_sentiment`：市场结构与情绪分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：计算指数、宽度、成交、涨跌分布、涨停结构和赚钱效应，声明范围与异常。
- 必需输入：指数成分、成交额、上涨/下跌/平盘、涨跌停、停牌、ST、新股样本及统一金额/数量单位。
- 前置依赖：依赖 data.standardization_quality 的统一字段、data.time_provenance 的交易日可得性和交易日历版本。
- 具体产物：市场宽度统计表、分母明细、涨跌分布、赚钱效应快照和缺口清单。
- 验收条件：分母可按股票清单复算；缺失不计为 0；停牌/ST/新股规则显式；历史成员版本一致且结果可重放。
- 指定复核：`market.method_validation`, `data.time_provenance`, `engineering.qa_review`
- 权限排除：不得把缺失当 0、混用指数范围、用未来成分重算历史或输出无证据的情绪结论。
- 缺失/冲突/失败交接：交给 data.time_provenance 与 market.method_validation；附样本范围、分母、缺口、规则版本和无法计算指标。

<a id="market-sector-theme"></a>
### `market.sector_theme`：板块与题材分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按版本化成员分解行业/概念强弱、贡献、主线、龙头和轮动，禁止未来成员回填。
- 必需输入：行业/概念成分有效区间、个股行情、资金流、板块分类版本和成分变更记录。
- 前置依赖：依赖 data.standardization_quality 的证券/板块映射、data.time_provenance 的成员生效时间和 market.structure_sentiment 的市场基准。
- 具体产物：板块强弱分解表、个股贡献表、资金聚合表、轮动证据链和版本化成分清单。
- 验收条件：历史计算只使用当时有效成员；贡献合计可复算；成员变更不倒灌；资金单位、采样粒度和缺口均显式。
- 指定复核：`market.structure_sentiment`, `market.method_validation`, `data.time_provenance`
- 权限排除：不得把当前成员回填历史、混淆行业与概念、把聚合值当个股事实或隐去未覆盖成分。
- 缺失/冲突/失败交接：交给 data.standardization_quality 与 market.method_validation；附成员版本、贡献差异、资金口径和缺失成分。

<a id="market-fund-flow-lhb"></a>
### `market.fund_flow_lhb`：资金流与龙虎榜分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：保留供应商资金定义和单位，分析连续变化、板块聚合和龙虎榜关联。
- 必需输入：龙虎榜明细、主力净流入/流出、成交额、席位与证券映射、交易日期和金额单位。
- 前置依赖：依赖来源权限核验、证券实体映射、交易日历和 data.time_provenance 的可得时间。
- 具体产物：资金流明细表、龙虎榜证据卡、日/板块聚合结果、重复记录报告。
- 验收条件：单位换算可复算；同一记录去重规则可解释；龙虎榜日期与公告可得时间一致；缺失席位不补造。
- 指定复核：`market.method_validation`, `data.time_provenance`, `engineering.qa_review`
- 权限排除：不得把净流入当成交额、把席位推断成持仓事实、跨日拼接不明记录或覆盖有效明细。
- 缺失/冲突/失败交接：交给 data.standardization_quality 与 market.sector_theme；附原始记录、映射、重复键、聚合差异和受影响日期。

<a id="market-technical"></a>
### `market.technical`：个股技术分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：在固定复权时序上计算趋势、支撑压力、波动和信号，明确触发与失效。
- 必需输入：日线/分钟 OHLCV、复权因子、停牌标记、个股资料、交易日历和行情可得时间。
- 前置依赖：依赖 data.standardization_quality 的价格单位、data.time_provenance 的 cutoff、market.structure_sentiment 的范围规则。
- 具体产物：指标计算表、支撑/压力事件、技术筛选结果、复权版本和信号解释。
- 验收条件：指标公式、窗口、复权和缺失处理可重算；停牌不生成虚假价格；信号只使用 cutoff 前数据。
- 指定复核：`market.method_validation`, `data.time_provenance`, `engineering.qa_review`
- 权限排除：不得偷看未来 K 线、把停牌补为零成交、混用前后复权或将技术信号直接当订单。
- 缺失/冲突/失败交接：交给 data.time_provenance 与 market.method_validation；附证券、窗口、K 线、公式版本、缺口和信号影响。

<a id="market-financial-valuation"></a>
### `market.financial_valuation`：公司财务与估值分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按公告发布日期核对报表、盈利质量、现金流、负债、估值和同行可比性。
- 必需输入：财报原始字段、公告发布时间、TTM/季度口径、价格、行业可比样本和会计期间。
- 前置依赖：依赖 data.time_provenance 的公告可得时间、data.standardization_quality 的单位/币种和 market.corporate_action 的股本变更。
- 具体产物：估值指标表、TTM/同比计算底稿、可比公司样本、异常值和口径说明。
- 验收条件：只纳入 cutoff 前已公告数据；分母为零、重述和缺失单独标记；每个指标可从原始字段复算。
- 指定复核：`data.time_provenance`, `market.method_validation`, `engineering.qa_review`
- 权限排除：不得用后来重述替换当时版本、把缺报补成零、混用财年口径或输出确定性投资结论。
- 缺失/冲突/失败交接：交给 data.time_provenance 与 market.method_validation；附公告时间、报表版本、公式、异常分母和受影响指标。

<a id="market-news-event"></a>
### `market.news_event`：新闻电报与事件分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按发布时间归并新闻，维护主题、标的映射、确认状态、冲突和事件日历。
- 必需输入：新闻电报、公告正文/摘要、发布时间与采集时间、来源许可、股票/板块候选映射。
- 前置依赖：依赖 provider 去重能力、实体映射规则、data.time_provenance 和人工复核入口。
- 具体产物：新闻时间线、来源引用、主题/实体映射、确认状态和去重关联表。
- 验收条件：相同事件保留去重依据；发布时间与采集时间分开；未确认消息单独标记；正文许可和来源可追溯。
- 指定复核：`data.time_provenance`, `report.adversarial_review`, `engineering.qa_review`
- 权限排除：不得把摘要扩写成事实、把流言改为确认、抓取无许可正文或覆盖用户收藏状态。
- 缺失/冲突/失败交接：交给 data.time_provenance、market.corporate_action 与 report.adversarial_review；附原文、映射候选、冲突和确认缺口。

<a id="market-corporate-action"></a>
### `market.corporate_action`：公司公告与公司行动分析

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：记录公告、业绩预告、分红、增减持、解禁的发布日期、生效日期和修订版本。
- 必需输入：公告、分红送转、配股/增发、停复牌、实施日、除权日、修订版本和证券映射。
- 前置依赖：依赖新闻来源、data.time_provenance 的公告/实施时间和 data.standardization_quality 的证券事件 schema。
- 具体产物：公司行动台账、有效期区间、复权因子、事件修订链和影响价格清单。
- 验收条件：公告时间、实施时间和除权时间分列；复权因子可复算；修订保留版本；未生效事件不得改写历史行情。
- 指定复核：`data.time_provenance`, `market.method_validation`, `engineering.qa_review`
- 权限排除：不得用发布日期代替生效日、把传闻当公司行动、静默修改历史因子或跨证券复制事件。
- 缺失/冲突/失败交接：交给 data.time_provenance 与 market.technical；附公告、事件状态、日期差异、因子计算和受影响证券。

<a id="market-method-validation"></a>
### `market.method_validation`：特色指标与方法验证

- 分组 / 最低阶段 / 模式：`market` / `2` / `design`
- 允许阶段范围：`2/3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：建立特色指标公式、样本、版本和限制，检验稳定性；未通过只能标实验。
- 必需输入：市场指标公式、样本快照、期望值、极端/空样本、历史版本和误差容忍度。
- 前置依赖：依赖 market 各专业产物、data.time_provenance 的样本切分和 quant.independent_evaluation 的独立评估规则。
- 具体产物：公式规范、样本重算表、边界测试报告、误差解释和未通过指标清单。
- 验收条件：每个指标能由输入复算；空样本、分母零、停牌和修订有明确结果；未通过项不得进入正式报告。
- 指定复核：`quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得只测正常样本、把数值接近当口径一致、替实现者改期望值或宣称策略有效。
- 缺失/冲突/失败交接：交给对应 market 角色、report.adversarial_review 与 quant.independent_evaluation；附失败样本、误差、版本和阻断结论。

<a id="report-pre-open"></a>
### `report.pre_open`：盘前策略

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：只用盘前截止快照生成情景、关注方向、观察条件和失效条件；冻结后不可回填。
- 必需输入：前一交易日结算、08:30 需求截止、08:45 采集窗口、08:50 冻结规则、事件/行情快照和预测模板。
- 前置依赖：依赖 data.time_provenance 的可得时间、market 产物、worker 采集批次和 snapshot_id 冻结账本。
- 具体产物：盘前报告草稿、08:50 冻结快照、证据索引、缺失项和预测版本。
- 验收条件：严格记录 08:30 截止、08:45 采集、08:50 冻结；冻结后拒绝新信息；缺失项不补造且可重放。
- 指定复核：`data.time_provenance`, `report.adversarial_review`, `report.editorial_final`
- 权限排除：不得读取截止后信息、修改冻结 snapshot_id、把未核验消息写成事实或发出交易指令。
- 缺失/冲突/失败交接：交给 PM、data.time_provenance 与 report.adversarial_review；附截止判定、采集批次、缺失字段、冻结状态和预测影响。

<a id="report-intraday"></a>
### `report.intraday`：盘中跟踪

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：以时间戳追加盘前条件触发、行情/事件变化和新增证据，不改写冻结稿。
- 必需输入：盘中行情增量、事件增量、available_at、前版冻结报告、T 观察卡片和变更原因。
- 前置依赖：依赖行情时钟、market.news_event 去重、前版 snapshot_id 和 report.adversarial_review 复核。
- 具体产物：盘中增量报告、观点修订记录、证据时间线、未确认事件列表和提醒状态。
- 验收条件：每条新增证据有来源和时间；修订保留前后文本；未确认事件不得成为事实；超时数据被拒绝。
- 指定复核：`data.time_provenance`, `report.adversarial_review`, `report.editorial_final`
- 权限排除：不得越过 cutoff、代替订单执行、删除前版结论或把 AI 解读当原始证据。
- 缺失/冲突/失败交接：交给 report.adversarial_review 与 data.time_provenance；附增量证据、修订差异、未确认事件和影响判断。

<a id="report-post-close"></a>
### `report.post_close`：盘后复盘

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：用冻结稿、盘中记录和收盘证据解释差异，把事后因果保留为假设。
- 必需输入：收盘行情/事件快照、全天报告版本、实际交易记录引用、异常日志和复盘范围。
- 前置依赖：依赖收盘时间确认、market.method_validation、个人资产归属规则和前后版本关联。
- 具体产物：盘后复盘报告、事实/解释/建议分层表、交易关联索引和未决事项清单。
- 验收条件：引用完整；事实与解释分层；交易记录只读引用；缺失/冲突显式展示；复盘可从收盘快照重算。
- 指定复核：`data.time_provenance`, `report.adversarial_review`, `report.editorial_final`
- 权限排除：不得改写历史成交、补造未采集事实、把建议写成已执行订单或覆盖用户原笔记。
- 缺失/冲突/失败交接：交给 report.adversarial_review、personal.trade_record_discipline 与 PM；附收盘快照、引用缺口、版本差异和争议。

<a id="report-prediction-settlement"></a>
### `report.prediction_settlement`：预测结算与研究评估

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按版本化规则独立结算命中、失效或无法判定，不能改写原判断。
- 必需输入：08:50 冻结预测、实际结果、结算窗口、样本标签、不可用标记和历史预测版本。
- 前置依赖：依赖 report.pre_open 的冻结包、data.time_provenance、结算时钟和独立评估样本规则。
- 具体产物：预测结算表、命中/偏差分类、不可用样本清单、重算批次和准确率底稿。
- 验收条件：冻结预测不可回写；结果仅在可得后结算；未结算不计入准确率；重算保留原指标和原因。
- 指定复核：`data.time_provenance`, `quant.independent_evaluation`, `report.editorial_final`
- 权限排除：不得用盘后信息重写原预测、把缺失结果计为对错或调整样本选择迎合指标。
- 缺失/冲突/失败交接：交给 data.time_provenance、report.adversarial_review 与 quant.independent_evaluation；附冻结版本、结算时间、不可用原因和指标变化。

<a id="report-adversarial-review"></a>
### `report.adversarial_review`：反方审查

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：逐项寻找替代解释、反证、时间穿越、样本偏差和遗漏风险，提出可复现意见。
- 必需输入：待审报告、原始引用、snapshot_id/cutoff、计算底稿、修订记录和作者说明。
- 前置依赖：依赖所有上游报告/市场产物可追溯，且评审者不承担被审内容的实现责任。
- 具体产物：事实核查清单、时间穿越/偏差/缺证问题单、通过/阻断结论和整改复核记录。
- 验收条件：能发现未来信息、来源缺失、数字不可复算、幸存者偏差和叙述过度；每个问题有证据定位。
- 指定复核：`quant.independent_evaluation`, `report.editorial_final`, `engineering.qa_review`
- 权限排除：不得替作者重写结论、用个人判断掩盖证据缺口或跳过阻断项放行。
- 缺失/冲突/失败交接：交给 report.editorial_final 与原实现角色；附问题级证据、严重度、整改条件和复核截止。

<a id="report-editorial-final"></a>
### `report.editorial_final`：报告审校与终稿复核

- 分组 / 最低阶段 / 模式：`report` / `3` / `design`
- 允许阶段范围：`3`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：核对数字、引用、截止、事实/意见分层和反方处理，决定通过、退回或部分发布。
- 必需输入：通过 adversarial review 的报告稿、证据矩阵、引用索引、未决问题和用户可见范围。
- 前置依赖：依赖 report.adversarial_review 的放行结论、PM 版本规则和个人资产隔离策略。
- 具体产物：终稿 Markdown/结构化版本、引用索引、假设与限制段、发布版本号和审校日志。
- 验收条件：事实、计算、AI 解读和个人记录分层；阻断问题未关闭不得发布；每项数字和引用可追溯。
- 指定复核：`report.adversarial_review`, `engineering.qa_review`, `pm`
- 权限排除：不得删反例、隐去缺失、改变冻结事实、暴露私有记录或把设计稿称为已实现。
- 缺失/冲突/失败交接：交给 PM 与 report.adversarial_review；附终稿差异、未关闭问题、缺失引用和可发布条件。

<a id="personal-research-management"></a>
### `personal.research_management`：个人研究管理

- 分组 / 最低阶段 / 模式：`personal` / `2` / `design`
- 允许阶段范围：`2`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：维护用户股票池、自选、笔记、标签、收藏和上下文版本，手工资产不被自动内容覆盖。
- 必需输入：用户自有股票池、研究笔记、标签、收藏、导入文件、版本和工作区归属。
- 前置依赖：依赖身份/空间隔离、backend API、数据标准化契约和显式导入确认。
- 具体产物：版本化研究条目、股票池成员历史、标签索引、导入预览和归属审计记录。
- 验收条件：跨用户不可见；导入先预览；删除/合并可追溯；自动生成内容与手工笔记分层；不覆盖已有个人配置。
- 指定复核：`engineering.security_ops`, `engineering.backend_api`, `engineering.qa_review`
- 权限排除：不得读取他人资产、把公开行情写成用户笔记、无确认批量覆盖或保存 provider 密钥。
- 缺失/冲突/失败交接：交给 engineering.backend_api 与 PM；附用户/空间、导入批次、冲突记录、原版本和恢复步骤。

<a id="personal-monitor-alerts"></a>
### `personal.monitor_alerts`：监控与提醒

- 分组 / 最低阶段 / 模式：`personal` / `2` / `design`
- 允许阶段范围：`2`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：定义价格、指标和事件提醒的触发、去重、确认、解除和失败状态，绑定用户与时间。
- 必需输入：用户阈值、行情/指标事件、去重键、通知偏好、确认状态和失败重试记录。
- 前置依赖：依赖 market.technical、worker 任务状态、用户时区和通知通道契约。
- 具体产物：提醒规则、触发事件、去重/确认状态、通知回执和失败队列。
- 验收条件：同一事件只触发一次或按规则重复；状态转换可追溯；行情缺失不触发误报；失败可重试且不丢确认。
- 指定复核：`engineering.worker`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得替用户下单、跨用户发送通知、用旧行情触发新提醒或把发送失败标为已送达。
- 缺失/冲突/失败交接：交给 engineering.worker 与 engineering.security_ops；附规则、事件时间、投递回执、重试次数和用户影响。

<a id="personal-trade-record-discipline"></a>
### `personal.trade_record_discipline`：交易记录与纪律复盘

- 分组 / 最低阶段 / 模式：`personal` / `2` / `design`
- 允许阶段范围：`2`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：解析核对私有成交记录，对照事前计划评估纪律偏差，解析与确认分离。
- 必需输入：用户交易流水、券商导出/文本、成交时间、证券代码、数量价格、手续费和人工纠错。
- 前置依赖：依赖用户归属、文本解析器、report.post_close 的复盘索引和只读原始文件。
- 具体产物：标准交易台账、解析置信度、人工确认队列、复盘关联和纠错审计。
- 验收条件：原始文件保留；解析字段可回溯；未确认行不计入收益；修改有操作者和前后值；不混入模拟交易。
- 指定复核：`report.post_close`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得伪造成交、覆盖原始导出、把文本猜测写成确认或向外部发送交易数据。
- 缺失/冲突/失败交接：交给 personal.research_management、report.post_close 与 PM；附原文、解析错误、未确认行、收益影响和纠错建议。

<a id="quant-strategy-research"></a>
### `quant.strategy_research`：量化策略研究

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：提出可证伪因子/信号假设，冻结参数、基准、样本划分、费用口径和失效标准。
- 必需输入：研究假设、因子定义、point-in-time 特征、样本切分、费用/滑点假设、程序/引擎接口和实验计划。
- 前置依赖：依赖 data.time_provenance、strategy implementation API、实验登记和冻结策略；未经登记不得运行。
- 具体产物：策略规格、因子字典、样本协议、版本锁清单、失败候选和研究决策记录。
- 验收条件：数据/程序/引擎版本、样本外边界、费用假设和失败候选均冻结可复现；结论不越过设计阶段。
- 指定复核：`quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得使用未来特征、未登记因子、真实交易权限或把研究候选当生产策略。
- 缺失/冲突/失败交接：交给 quant.strategy_implementation 与 quant.independent_evaluation；附假设、特征版本、样本、失败候选和阻断问题。

<a id="quant-strategy-implementation"></a>
### `quant.strategy_implementation`：量化程序开发

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：忠实实现冻结策略规格为确定性程序，固定参数、信号、持仓和行为测试。
- 必需输入：策略规格、程序 API、引擎 API、参数 schema、冻结数据/程序/引擎版本和合成行情。
- 前置依赖：依赖 strategy_research 冻结包、backend/worker 接口、数据时间语义、确定性运行环境和资源边界。
- 具体产物：策略程序包、接口请求/响应样例、参数校验器、版本锁和失败候选日志。
- 验收条件：程序与引擎接口可重放；数据、程序、引擎版本完全锁定；参数错误显式拒绝；失败候选保留。
- 指定复核：`quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得绕过统一数据访问层、动态换版本、读取真实密钥或连接券商/订单接口。
- 缺失/冲突/失败交接：交给 quant.strategy_research、quant.backtest_engine 与 engineering.backend_api；附接口、版本锁、错误日志和未满足契约。

<a id="quant-backtest-engine"></a>
### `quant.backtest_engine`：回测引擎开发

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现时间推进、撮合、停牌/涨跌停、费用、滑点、收益核算和可重放对账。
- 必需输入：交易日历、复权行情、停牌/ST规则、手续费、滑点、策略版本、参数、随机种子和异常交易样本。
- 前置依赖：依赖 strategy_implementation 的程序/引擎接口、point-in-time 数据、冻结实验配置和回放环境。
- 具体产物：回测运行包、成交明细、收益/风险指标、费用明细、异常交易和失败候选。
- 验收条件：回测可按输入重放；费用/滑点/停牌/复权/交易日正确；无未来数据、幸存者偏差；失败结果不删除。
- 指定复核：`quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得偷看未来、忽略费用、只留幸存证券、手工改收益曲线或把回测当实盘。
- 缺失/冲突/失败交接：交给 quant.experiment_execution 与 quant.independent_evaluation；附输入快照、引擎版本、异常成交、偏差检查和失败候选。

<a id="quant-experiment-execution"></a>
### `quant.experiment_execution`：回测实验执行

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：用冻结代码、数据和配置运行实验，保存交易明细、指标、资源状态和失败候选。
- 必需输入：实验登记、冻结数据/程序/引擎版本、资源/费用预算、指标定义、候选策略和运行参数。
- 前置依赖：依赖 strategy_implementation、backtest_engine、实验冻结策略、运行账本和成本上限。
- 具体产物：run_id、运行日志、指标快照、资源/费用消耗、失败候选目录和重跑条件。
- 验收条件：每次运行可复现且版本齐全；失败候选、异常退出、预算超限和输出缺失均可观测并阻断发布。
- 指定复核：`quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得运行中换数据/代码、删除失败运行、突破预算或发布未登记结果。
- 缺失/冲突/失败交接：交给 quant.independent_evaluation 与 engineering.worker；附 run_id、版本锁、日志、资源费用、失败候选和重跑条件。

<a id="quant-independent-evaluation"></a>
### `quant.independent_evaluation`：独立策略评估

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：独立复现实验，检查未来信息、幸存者偏差、参数选择、敏感性和样本外表现。
- 必需输入：冻结实验包、样本外数据、作者/实验执行者名单、评估计划、泄露审计、幸存者审计、多试验记录和费用敏感性参数。
- 前置依赖：依赖独立评估者指派、实验登记、样本外切分和只读冻结数据；评估者不得是作者或实验执行者。
- 具体产物：独立评估报告、样本外指标、泄露/幸存者/多试验/费用敏感性审计和否决理由。
- 验收条件：明确由本角色承担评估；作者和执行者不得兼任；报告样本外表现、泄露、幸存者偏差、多试验和费用敏感性。
- 指定复核：`report.adversarial_review`, `quant.portfolio_risk`, `engineering.qa_review`
- 权限排除：不得修改冻结数据、挑选有利指标、由作者/执行者自评或接触真实交易权限。
- 缺失/冲突/失败交接：交给 PM、quant.strategy_research 与 quant.experiment_execution；附独立性声明、审计证据、否决项和补验条件。

<a id="quant-paper-trading-drift"></a>
### `quant.paper_trading_drift`：模拟交易与偏差监控

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：对比实时信号/模拟成交与回测，监控延迟、滑点、数据漂移和异常，不接触真实资金。
- 必需输入：冻结策略信号、模拟成交、实时行情、延迟/滑点、基准回测、模拟账户状态和漂移阈值。
- 前置依赖：依赖策略/引擎版本锁、实时可得时间、模拟账户隔离和 quant.independent_evaluation 的基准结果。
- 具体产物：信号-成交对齐表、延迟/滑点统计、收益漂移指标、异常时间窗和暂停建议。
- 验收条件：每个信号可对齐模拟成交；延迟、滑点、缺失和漂移可重算；超阈值自动生成暂停建议。
- 指定复核：`quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得把模拟成交当真实成交、连接真实账户、掩盖延迟或手工删除异常窗口。
- 缺失/冲突/失败交接：交给 quant.strategy_implementation、quant.portfolio_risk 与 PM；附对齐样本、漂移指标、版本差异和暂停条件。

<a id="quant-portfolio-risk"></a>
### `quant.portfolio_risk`：投资组合与风险

- 分组 / 最低阶段 / 模式：`quant` / `4` / `design`
- 允许阶段范围：`4`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按独立规则检查仓位、集中度、相关暴露、流动性、损失限额和压力场景。
- 必需输入：策略候选、用户持仓/本金口径、相关性、行业暴露、集中度、止损、压力场景和风险限额。
- 前置依赖：依赖独立评估结论、个人资产归属、风险参数版本、模拟漂移结果和执行隔离。
- 具体产物：风险暴露表、压力损失、仓位上限、止损/拒绝条件和需用户确认的建议。
- 验收条件：建议含暴露/集中度/压力损失/限额依据；超限必拒绝；建议与真实订单完全分离并可追溯。
- 指定复核：`quant.independent_evaluation`, `execution.independent_risk`, `engineering.qa_review`
- 权限排除：不得读取他人持仓、替用户下单、绕过风险限额或把建议仓位当授权指令。
- 缺失/冲突/失败交接：交给 execution.independent_risk、quant.independent_evaluation 与 PM；附风险输入、超限项、场景结果和拒绝理由。

<a id="execution-order-engineering"></a>
### `execution.order_engineering`：订单执行工程

- 分组 / 最低阶段 / 模式：`execution` / `5` / `design`
- 允许阶段范围：`5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：在另行授权下实现券商适配、幂等订单状态、成交对账、停止和恢复，动作可审计。
- 必需输入：已授权订单意图、证券/方向/数量/价格、账户权限、幂等键、券商接口契约和停止信号。
- 前置依赖：依赖 execution.independent_risk 放行、broker adapter 契约、订单状态机、密钥托管和人工确认门。
- 具体产物：订单状态机、幂等请求、回报映射、撤单/暂停/恢复记录和审计日志。
- 验收条件：未获授权或风控放行不得发送；重复请求不重复下单；部分成交、拒单、超时和恢复状态可观测。
- 指定复核：`execution.independent_risk`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得保存明文密钥、绕过风控、调用未注册券商或把模拟订单写入真实账本。
- 缺失/冲突/失败交接：交给 execution.independent_risk、engineering.security_ops 与 PM；附订单意图、幂等键、回报、状态和停止原因。

<a id="execution-independent-risk"></a>
### `execution.independent_risk`：独立执行风控

- 分组 / 最低阶段 / 模式：`execution` / `5` / `design`
- 允许阶段范围：`5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：独立核验资金、仓位、价格、时效、限额和停止开关，缺字段默认拒绝。
- 必需输入：账户余额、持仓、价格新鲜度、单笔/日限额、流动性、策略风险结果和停止条件。
- 前置依赖：依赖 quant.portfolio_risk、订单意图、账户只读接口、风险参数版本和独立审批。
- 具体产物：盘前/盘中风控判定、限额计算、拒绝原因、需要人工确认的清单和风险事件。
- 验收条件：任一关键输入缺失或过期即 fail-closed；限额和价格可复算；拒绝不可被订单角色覆盖。
- 指定复核：`quant.portfolio_risk`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得替订单角色放行、修改持仓事实、降低限额或接收无来源账户数据。
- 缺失/冲突/失败交接：交给 execution.order_engineering、quant.portfolio_risk 与 PM；附输入时间、限额计算、拒绝原因和恢复门槛。

<a id="execution-strategy-operations"></a>
### `execution.strategy_operations`：策略运行与维护

- 分组 / 最低阶段 / 模式：`execution` / `5` / `design`
- 允许阶段范围：`5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：监测策略任务、数据漂移、退化和运行偏差，不静默改变批准策略或风控。
- 必需输入：已评估策略版本、运行状态、收益/回撤、漂移指标、风控事件、暂停/恢复授权和操作日历。
- 前置依赖：依赖 quant.paper_trading_drift、execution.independent_risk、订单状态日志和 PM 的策略启停决定。
- 具体产物：策略运行台账、暂停/恢复记录、漂移告警、操作复盘和长期维护变更单。
- 验收条件：漂移/回撤/风控超限触发暂停；恢复需新批准和版本校验；每次操作有操作者、时间和理由。
- 指定复核：`execution.independent_risk`, `quant.independent_evaluation`, `engineering.qa_review`
- 权限排除：不得自行改策略参数、绕过暂停、隐藏亏损或把设计候选当长期实盘策略。
- 缺失/冲突/失败交接：交给 PM、execution.independent_risk 与 quant.independent_evaluation；附运行版本、风险事件、操作日志和恢复条件。

<a id="engineering-architecture"></a>
### `engineering.architecture`：架构

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：维护模块边界、共享契约、阶段门槛、时间/权限决策和 ADR，阻止跨阶段集成。
- 必需输入：模块契约、ADR、数据流、角色覆盖、阶段门槛、威胁模型和外部依赖清单。
- 前置依赖：依赖 PM 的范围决定、boss 的阶段授权和各模块输入输出；冲突必须形成新 ADR。
- 具体产物：架构图、边界/依赖矩阵、ADR、阶段 gate、数据访问与权限决策记录。
- 验收条件：无隐式跨层调用、无旧项目运行依赖、每项边界有责任人和回滚/失败路径；ADR 可审查。
- 指定复核：`engineering.qa_review`, `engineering.security_ops`, `pm`
- 权限排除：不得凭空扩大阶段、把架构设计当实现完成或授予角色工具、密钥和交易权限。
- 缺失/冲突/失败交接：交给 PM 与 boss；附冲突 ADR、受影响模块、替代方案、阻断依赖和待决问题。

<a id="engineering-frontend-interaction"></a>
### `engineering.frontend_interaction`：前端与交互

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现页面、图表、表单和移动布局，准确呈现缺失、过期、失败和归属状态。
- 必需输入：API schema、页面状态、字段时间/缺失语义、交互需求、权限边界和可访问性要求。
- 前置依赖：依赖 backend_api 的稳定契约、architecture 的导航边界、personal 归属规则和设计验收样例。
- 具体产物：页面/组件状态矩阵、请求响应映射、空/缺失/错误/加载交互、前端验收用例。
- 验收条件：加载、空数据、部分失败、过期和权限拒绝均可见；不伪造数值；用户资产只显示给归属用户。
- 指定复核：`engineering.backend_api`, `engineering.qa_review`, `engineering.security_ops`
- 权限排除：不得页面直连 provider、在前端保存密钥、用零值掩盖缺失或绕过后端权限。
- 缺失/冲突/失败交接：交给 engineering.backend_api 与 engineering.qa_review；附页面、请求、状态、复现步骤和用户影响。

<a id="engineering-backend-api"></a>
### `engineering.backend_api`：后端 API

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现查询、领域服务、归属过滤和显式任务入口，普通读取不得隐式采集或调用 AI。
- 必需输入：模块 API 契约、身份/权限、统一数据访问接口、分页/时间参数、错误码和审计需求。
- 前置依赖：依赖 architecture 边界、database schema、worker 状态和 provider adapter；禁止页面或 Agent 直取 provider。
- 具体产物：OpenAPI/请求响应 schema、权限校验、分页游标、错误模型、审计事件和契约测试。
- 验收条件：所有数据经统一访问层；缺失/失败不覆盖有效记录；权限、分页、cutoff、错误码和审计事件可测试。
- 指定复核：`engineering.architecture`, `engineering.database`, `engineering.qa_review`
- 权限排除：不得打印 token、隐式建表、导入旧初始化模块或返回未脱敏 provider 响应。
- 缺失/冲突/失败交接：交给 engineering.database、engineering.worker 与 engineering.qa_review；附 endpoint、请求、状态码、数据层错误和回滚方案。

<a id="engineering-database"></a>
### `engineering.database`：数据库工程

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：用显式迁移实现模型、revision、索引、归属约束、幂等发布和备份恢复。
- 必需输入：领域 schema、血缘/归属字段、Alembic revision、索引、保留策略、备份和恢复样本。
- 前置依赖：依赖 architecture 数据边界、backend API 读写契约、historical_migration 的隔离要求和 security_ops 的备份策略。
- 具体产物：显式 Alembic 迁移、表/索引设计、约束、回滚脚本、备份恢复记录和数据字典。
- 验收条件：应用导入不建表；迁移可升级/回滚；归属与血缘约束生效；恢复后数据与审计一致；有效记录不被失败覆盖。
- 指定复核：`engineering.architecture`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得改旧库、隐式 create_all、删除未迁移数据、以空值覆盖事实或绕过归属过滤。
- 缺失/冲突/失败交接：交给 architecture、data.historical_migration 与 engineering.qa_review；附 revision、SQL、失败事务、回滚点和数据影响。

<a id="engineering-worker"></a>
### `engineering.worker`：作业与 worker 工程

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：实现任务依赖、原子领取、lease/fencing、重试、取消和恢复，过期 worker 不能写入。
- 必需输入：任务 schema、依赖图、lease/fencing、重试/取消策略、幂等键、provider 状态和运行预算。
- 前置依赖：依赖 backend_api、database、source_ingestion 的状态契约及 observability/告警配置。
- 具体产物：任务状态机、调度/重试/取消记录、lease 心跳、失败队列、运行指标和恢复操作。
- 验收条件：429 按策略退避且有上限；重复任务幂等；取消可观测；失败不清空有效结果；进程重启可恢复 checkpoint。
- 指定复核：`engineering.backend_api`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得无限重试、并发写同一批次、绕过 fencing、把失败标成功或把秘密写入日志。
- 缺失/冲突/失败交接：交给 engineering.backend_api、data.source_ingestion 与 engineering.security_ops；附 job_id、状态转移、重试、checkpoint 和告警。

<a id="engineering-ai-workflow"></a>
### `engineering.ai_workflow`：AI 工作流工程

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：编排角色、白名单工具、证据引用、预算、结构化输出和运行审计。
- 必需输入：已核验事实/引用、提示词版本、模型配置、预算、输出 schema、失败样例和人工复核规则。
- 前置依赖：依赖 backend_api 的证据接口、report/editorial 边界、security_ops 脱敏和成本限额。
- 具体产物：AI 工作流图、提示词/模型版本、结构化输出、引用绑定、失败/降级状态和费用账本。
- 验收条件：输出只能引用输入事实；引用缺失、超预算、模型失败可见并降级；AI 解读与事实层分开；不泄露秘密。
- 指定复核：`report.adversarial_review`, `engineering.security_ops`, `engineering.qa_review`
- 权限排除：不得把模型输出写成原始事实、向未批准 provider 发送私有数据、绕过人工复核或持有交易权限。
- 缺失/冲突/失败交接：交给 report.adversarial_review、engineering.security_ops 与 PM；附输入引用、模型版本、错误、费用和降级结果。

<a id="engineering-qa-review"></a>
### `engineering.qa_review`：独立 QA／代码审查

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：独立 forward-test 候选入口，复现边界、失败、权限、时间和回归问题，不能自验收。
- 必需输入：需求契约、实现差异、测试结果、合成数据、权限/时间边界、失败日志和审查清单。
- 前置依赖：依赖各实现角色提供可重放证据；评审者不得验收自己实现的模块；阻断项需 PM 确认。
- 具体产物：独立 QA 报告、阻断缺陷、回归范围、证据定位、通过/拒绝结论和复验条件。
- 验收条件：覆盖正常、缺失、冲突、越权、cutoff、重试、回滚和失败路径；每个结论能复现；未通过不得放行。
- 指定复核：`engineering.architecture`, `engineering.security_ops`, `pm`
- 权限排除：不得用实现说明代替测试、替实现者修改结果、跳过失败日志或在证据不足时放行。
- 缺失/冲突/失败交接：交给 PM 与对应实现角色；附缺陷级复现、严重度、阻断门、修复负责人和复验条件。

<a id="engineering-security-ops"></a>
### `engineering.security_ops`：安全与运维

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：管理秘密、隔离、脱敏日志、备份恢复、部署和通知故障，执行最小权限。
- 必需输入：威胁模型、密钥/环境变量清单、脱敏规则、权限矩阵、审计日志、备份和恢复演练。
- 前置依赖：依赖 architecture 的边界、backend/worker 日志、database 备份、release 流程和通知配置。
- 具体产物：安全控制清单、脱敏规则与测试、最小权限矩阵、备份恢复报告、事故交接模板。
- 验收条件：token/个人资产/内部 URL 不出现在日志或响应；权限拒绝可审计；恢复演练成功；通知失败不泄密。
- 指定复核：`engineering.architecture`, `engineering.qa_review`, `engineering.integration_release`
- 权限排除：不得打印/提交密钥、读取不必要资产、关闭审计或把真实 provider 响应加入公开测试。
- 缺失/冲突/失败交接：交给 architecture、qa_review 与 PM；附风险、日志证据、影响范围、临时隔离和修复期限。

<a id="engineering-integration-release"></a>
### `engineering.integration_release`：集成与发布

- 分组 / 最低阶段 / 模式：`engineering` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：按发布锁合并，验证 exact SHA、版本、Actions、Release 和最终通知。
- 必需输入：待发布 commit/SHA、版本文件、verify/test 结果、公开资产清单、Release 草稿和通知状态。
- 前置依赖：依赖 qa_review 放行、security_ops 脱敏、PM 发布说明和 exact SHA/Actions 规则。
- 具体产物：发布清单、版本/标签、Actions 结果、Release 记录、通知回执和失败重跑说明。
- 验收条件：标签指向 exact GITHUB_SHA；0.x 为 prerelease；冲突不覆盖；失败不升版；main 只发送一次最终通知。
- 指定复核：`engineering.qa_review`, `engineering.security_ops`, `pm`
- 权限排除：不得发布未审查分支、输出密钥、覆盖已有版本、绕过 verify 或重复发送成功通知。
- 缺失/冲突/失败交接：交给 PM、qa_review 与 security_ops；附 SHA、Actions、Release/通知状态、冲突和可重跑条件。

<a id="boss"></a>
### `boss`：老板

- 分组 / 最低阶段 / 模式：`coordination` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：确认需求、阶段范围和发布授权，接收 PM 回执后释放对话。
- 必需输入：项目目标、阶段范围、预算/风险、架构冲突、审查结论和需要裁决的取舍。
- 前置依赖：依赖 PM 汇总、architecture 的影响分析和独立 QA/安全意见；没有证据的扩大范围不得授权。
- 具体产物：范围/阶段裁决、优先级、例外批准、阻断解除条件和决策日志。
- 验收条件：每个裁决有输入证据、责任人、阶段门和撤销条件；不把设计批准误报成实现完成。
- 指定复核：`pm`, `engineering.architecture`
- 权限排除：不得直接取得 provider 密钥、改写用户资产、绕过独立验收或授权未经评估的交易动作。
- 缺失/冲突/失败交接：交给 PM；附争议、证据缺口、影响模块、暂缓决定和再次提交条件。

<a id="pm"></a>
### `pm`：PM

- 分组 / 最低阶段 / 模式：`coordination` / `0` / `design`
- 允许阶段范围：`0-5`（`stage` 为工程派单可读取的最低执行阶段；角色模板仍属于阶段 0 设计契约）
- 负责需求：拆分业务专责、实现责任和独立验收，维护依赖、文件所有权、返工、集成、发布锁和汇报
- 必需输入：用户目标、项目计划、任务台账、角色覆盖 JSON/Markdown、独立审查意见和外部待验收状态。
- 前置依赖：依赖 boss 的范围授权、architecture 的边界、实现/业务角色的交接和 qa/security 的证据。
- 具体产物：任务派单包、三责映射、阶段门、交接记录、验收结论、风险台账和发布说明。
- 验收条件：每项任务都有业务专责/实现/独立验收；字段、stage、权限、失败交接和能力行可机器校验；阻断状态如实保留。
- 指定复核：`boss`, `engineering.architecture`, `engineering.qa_review`
- 权限排除：不得把角色契约当运行器、替角色读取秘密、跳过独立审查、用空结果掩盖未完成或擅改阶段范围。
- 缺失/冲突/失败交接：交给 boss 与对应责任角色；附任务 ID、缺失字段、依赖图、证据链接、阻断原因和下一步输入。

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

机器校验应检查：能力数 44；分组 data4/market8/report6/personal3/quant7/execution3/engineering9/coordination2；每角色契约字段非空；专业复核与工程复核均存在；`stage` 为整数最低阶段，`stage_range` 保留细分范围；实现与验收集合不相交；角色引用存在；每个 `template_ref` 都命中显式 anchor；JSON 与本表顺序和三责一致。
