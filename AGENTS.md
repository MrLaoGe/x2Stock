# XXStock Agent 工作约束

## 每轮接入顺序

1. 阅读 `README.md`、`docs/project-plan.md` 和 `docs/development/task-ledger.md`。
2. 查看 `git status --short`、当前分支和最近提交，保护不属于本轮的修改。
3. 阅读本轮模块文档、相关架构决策、数据契约及已有测试。
4. 说明本轮目标与将修改的边界，然后执行用户已经授权的工作。

## 当前阶段

当前为阶段 0：整体设计与文档仓库。未经后续模块任务扩展，不开发业务网页、采集服务、迁移程序、Agent 运行器或交易接口。配置示例与仓库校验工具属于本阶段交付。

用户已授权 Git/发布运维通知，当前默认 VoceChat #19。正式 main 批次由同一 `verify-docs` 工作流先验证、再发布 exact SHA 标签/Release、最后发送一次最终结果；main 与发布标签不另发 push 通知。开发分支与非发布标签保留 push 通知。推送后分别核验 Git、验证、Release 与通知结果，不额外手动发送重复消息。机器人地址与密钥保持本地/.env或GitHub Secrets，不能输出或提交。

## 数据与配置

- 允许来源为 Tushare、东方财富、财联社；zhitu、mairuiapi 只可在排除规则和旧审计事实中出现，不建立可调用适配器或凭据配置。
- 旧项目只读参考。不得 import 旧数据库/应用初始化模块，启动旧调度器，修改旧库，或者把旧路径作为新版运行依赖。
- 实际密钥只保存在用户的本地环境或部署 secrets；不打印、提交或向前端返回密钥，也不把带 token 的 MCP URL 写入日志。
- 原始数据、计算结果、AI 解读分层；缺失保持缺失，采集失败不得用空结果覆盖已有有效记录。
- 私有研究资产、个人记录和真实 provider 响应不得加入公开仓库；测试采用合成或已获明确发布授权的材料。

## 多 Agent 协作

- 用户已授权项目采用多 Agent；按任务复杂度启用数据、后端、前端和独立审查角色，小任务不强制并行。
- 并行写入使用独立分支/worktree，主 Agent 约定文件归属并负责集成，避免多人同时修改同一文件。
- 子 Agent 不自行推送、发布、改变阶段范围或修改旧项目；将结果和待解决问题交给主 Agent。
- 审查 Agent 先独立检查交付，再核对实现者说明；发现问题应给出证据和可验证修复。
- 开发 Agent 与未来产品内研究 Agent 是两套角色，不混用权限或状态。

## 项目 Skill 与版本发布

- 项目 Skill 放 `.agents/skills/<name>/SKILL.md`，在 `.agents/skills/registry.json` 登记分类、用途、状态和依赖；进入任务前查注册表并读取相应 Skill。规范见 [Skill 组织](docs/development/skills.md)。
- 开发与业务 Skill 分开；业务逻辑仍在后端/worker，Skill 不授予工具、写入、密钥或交易权限。不整包移植旧 3.0 Skill。
- 已授权正式 main 发布从 `0.1.0` 起每批默认 patch 加一，minor/major 需用户明确指定；根 VERSION 是唯一事实源。按 [github-release](.agents/skills/github-release/SKILL.md) 与 [发布规范](docs/development/releases.md) 准备版本及说明，并在提交前验证。
- 远端发布限正式 main push 的 Actions 和 exact `GITHUB_SHA`；0.x 为 prerelease 且非 latest。已有版本匹配时复用，冲突不覆盖；失败重跑不升版，通知歧义不盲重试。
- 推送前完成台账与交接并如实保留外部待验收状态；发布结果用 Actions 与用户输出报告，不追加成功记录提交触发下一版本。

## 技术和验证

- 前后端与 worker 通过新版业务服务、PostgreSQL 和统一数据访问层协作；不绕过适配器在页面或 Agent 中直接获取 provider 数据。
- 使用显式 Alembic 迁移；应用导入不得隐式建表或修复数据。
- 核心规则变动需更新 ADR、相关模块设计和验收条件，保留旧决策历史。
- 文档变更运行 `python scripts/verify_repository.py` 与 `git diff --check`。未来代码变更再运行对应模块测试、前端构建或后端检查，避免无关的全量测试。
- 不为简单文案新增镜像实现的测试。数据迁移、归属过滤、时间截止和订单风控需要行为测试。
- 修改 Git 通知或相关配置时运行 `python -m unittest discover -s tests -p 'test_*.py'`，覆盖脱敏、失败和消息行为；不在单元测试中使用真实机器人。

## 完成交接

更新任务台账，按 `docs/development/handoff-template.md` 记录最终状态、验证和遗留问题。明确区分已实现、设计确定和未验证。

用户在本轮已经授权初始提交及创建、发布 `MrLaoGe/XXStock` 文档仓库。后续提交、推送、发布按当轮用户授权执行；不存在授权时先完成可审查的本地成果。不得覆盖已存在的同名远端仓库。
