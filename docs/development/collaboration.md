# 多 Agent、多对话开发协作

## 老板与独立 PM

每项需求独立 PM；老板明确范围与任务内创建、消息、发布授权，确认真实 PM 对话后释放。PM 按依赖创建持久专业任务对话、自主安排并行，明确业务专责、实现、独立验收三责，处理退回与复验后自动集成已授权发布，主动返回老板。模板与本地协调工具见 [multi-dialogue-development](../../.agents/skills/multi-dialogue-development/SKILL.md)，职责与逐项覆盖见 [覆盖表](agent-coverage.md)。

执行者不得发布的规则不取消用户指定 PM 的发布责任。真实对话都是独立持久线程，关系记在任务记录；短 subagent 只能辅助。创建前 list_projects，选 XXStock 隔离 worktree，默认远端 main；执行角色从 PM 已提交基线接入自己的分支，新对话不指定模型覆盖。

异步创建先保存 client/operation 标识为 pending_creation，确认真实 threadId 后才跟进；状态不明核对原操作，不重复派发。取消先记录请求，执行者确认停止后才解除文件占用。缺失数据、证据冲突、工具失败报告 PM，保留原有效产物。

实时状态在 Git 公共目录下被忽略的 `.local/orchestration`，全 worktree 共享；包含授权、依赖、阶段、三责、对话 ID、分支/worktree/基线、文件归属、产物与候选评审。业务任务预留快照、截止和方法/策略版本，运行数据不能写入 Skill 或公开仓库。

多个 PM 可以并行，祖先/子目录共享路径也须明确所有者。发布锁绑定任务和 PM；无超时抢占。持锁后 fetch 最新 origin/main、集成复验，再按远端 VERSION 协调下一 patch。异常恢复核对原持有者、远端 Git/Actions/标签/Release/通知，不凭本地进程退出猜测失败；存在歧义保留锁。禁止 force push 和覆盖历史发布材料。

## 一轮任务的最小记录

开始时主 Agent 阅读总方案、台账和模块，核对当前 Git 状态；确定目标、验收、文件所有者与共享契约。无法从代码/文档确认的产品取舍再向用户询问，已确认决策不重复征求许可。

任务 ID 使用 `S阶段-序号`，状态为 `planned / in_progress / reviewed / completed / blocked`。`completed` 必须有产物和验证；发布状态单独记录，不能把本地完成写成已经发布。若来源/权限未经核验，保持 `unverified`。

## worktree 和集成

并行写入使用同一仓库下的独立分支/worktree。主 Agent 为各角色划定文件边界；共享文档、接口或 schema 由一个 Agent 主持，其他 Agent 提建议。创建 worktree 前检查是否存在适合本轮的可复用 checkout。

子 Agent 在自己的分支本地提交后返回提交 hash、修改范围与验证；不自行推送或发布。主 Agent 依次集成，解决冲突并重新跑与合并相关的检查。不要将工作树目录、临时核验数据或外部旧库纳入版本管理。确认集成和交接完整后可回收本轮 worktree。

## Skill 分工

项目 Skill 与文档一样指定单一写入所有者。新增 Skill 同步 `.agents/skills/registry.json` 的分类、用途、状态和依赖，主 Agent 集成后检查入口与引用。开发流程 Skill 和未来业务 Skill 分开；规范见 [Skill 组织](skills.md)，不能整包移植旧规则或放宽工具权限。

## 独立评审

审查 Agent 读取最终文档/代码、变更和验收要求，优先检查来源、用户归属、时间信息、回退、迁移副作用和公开资产。先独立找证据，再核对实现者总结。发现问题给出文件、触发条件、影响和验证方法；主 Agent 修复后补做定向核验。

简单文案不要求完整多 Agent 流程；数据迁移、隔离和报告时间边界应使用独立审查。多个角色采用同一模型不会自动消除相关性偏差。

## 多对话交接

每轮结束更新 [台账](task-ledger.md)，在 `docs/development/handoffs/` 增加交接记录。新对话以仓库文档和当前代码为准，不依赖上次聊天全文。

建议新对话请求：

```text
接入 XXStock，先读 README.md、AGENTS.md、docs/development/task-ledger.md
和本轮模块文档，核对 Git 状态。按已确认架构完成本轮授权工作，
记录输入输出、来源和验证结果，更新台账与交接，不修改旧项目。
本轮模块：[填写模块/任务 ID]
本轮目标：[填写具体交付]
```

## 发布

发布前检查待提交文件清单、文档链接、配置和凭据泄露模式。公开仓库不携带个人研究数据、真实接口响应或旧 Git 历史。用户授权发布后执行，不因通用流程再次请求同一许可；遇到认证缺失或远端名称冲突时报告实际障碍。

Git 提交作者使用项目公开身份。初始设计参考由项目作者提供的旧项目，第三方源码若后来提取必须登记许可，不默认全部可改成 MIT。

每批正式 main 发布使用 [github-release](../../.agents/skills/github-release/SKILL.md) 准备版本与说明；根 VERSION 为唯一版本源，从 `0.1.0` 起默认 patch 加一，用户明确指定才改变 minor/major。主 Agent 将版本材料、台账、交接和测试结果一起集成，提交前完成独立审查。

[发布工作流](releases.md) 按验证 → exact SHA 标签/Release → 最终通知执行；正式 main 与发布标签不另发 push 通知。开发分支和非发布标签保持独立 [push 通知](git-notifications.md)。只读通知 job 不共享 release job 的写权限，机器人秘密不进入 PR。

推送后分别报告 Git、校验、Release 与通知结果。失败重跑保持同一版本，已有发布冲突不覆盖；通知歧义先核对频道，不手动重复发送。成功结果使用 Actions 和用户输出记录，不再追加成功提交。秘密只通过本地环境或加密仓库 Secrets 管理。
