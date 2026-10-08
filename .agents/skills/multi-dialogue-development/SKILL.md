---
name: multi-dialogue-development
description: "在 XXStock 按老板派单、独立 PM、专业任务对话组织模块开发，维护责任、依赖、独立验收、返工和串行发布。仅开发协作；金融角色模板不构成业务运行器或交易授权。"
---

# 多对话开发

先读 README、AGENTS、台账、模块清单、路线和 Skill 注册表，核对 Git、origin/main 与人类授权。保留任务内已有授权；Skill 本身不授权创建、消息或发布。

## 按当前身份接入

- 老板：明确任务、范围与发布授权；先 list_projects，再 create_thread 创建每项需求独立 PM。确认真实 threadId 后交付回执并释放，不等待业务完成。异步只有 clientThreadId 时记录待确认，不能重复创建或当作真实 ID 发消息。
- PM：阅读 [调度与状态契约](references/orchestration.md)，拆分业务专责、工程实现、独立验收，按依赖创建持久专业对话。用角色模板选择实际责任，维护文件所有权，集成并复验；具有本任务发布授权的 PM 负责最终发布，不退回老板代办。
- 业务专责：阅读 [角色模板](references/roles.md) 中对应角色，定义输入、规则、验收与缺口。未来阶段仅设计职责，不运行尚未授权业务。
- 工程执行：按派发范围在隔离 worktree/分支实现；返回局部提交、产物和验证，不能推送发布或改其他 checkout。
- 独立审查：从真实需求和候选入口独立 forward-test，再核对实现说明；只读审查、给证据和复现步骤。不得用作者自评或多数同意替代验收。

## 交付约束

每项任务使用 [派发与交接模板](references/task-template.md)，根据 [模块责任覆盖](../../../docs/development/agent-coverage.md) 确定三责。短 subagent 可以辅助，不能替代用户要求的持久专业对话；父子关系由任务记录维护，UI 不具有层级树承诺。

真实对话用 Codex create_thread/send_message_to_thread/wait_threads；本地辅助脚本只维护状态，不伪造跨对话 API。新对话不覆盖模型，沿用用户配置。create_thread 前 list_projects；写入角色使用 XXStock 项目的独立 worktree，并从 PM 已提交约定基线接入。

实时记录在 Git 公共目录下被忽略的 `.local/orchestration`，不在 Skill 中放运行数据。发布前取得锁，fetch 最新 origin/main，集成后重新独立验收，调用 [github-release](../github-release/SKILL.md)。锁无超时抢占；异常先核对持有者和远端。取消请求不等于已停止。阶段、时间冻结、独立验收和权限均以契约及行为检查执行，不能只靠提示词。
