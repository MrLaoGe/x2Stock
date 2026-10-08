# 调度与状态契约

这是阶段 0 的开发辅助工具，不是业务 Agent 调度器或常驻服务。实现位于
`scripts/orchestration.py`，只使用 Python 标准库，不调用或伪造 `create_thread`。

全 worktree 通过 `git rev-parse --git-common-dir` 解析同一个
`common_dir/.local/orchestration`。`state.json` 使用临时文件加 `os.replace` 原子写入，
短写锁使用 `O_EXCL`；锁忙时失败，不按超时抢占。状态保存老板/PM/专业真实 ID、角色
阶段、授权、依赖、状态、worktree/分支/基线、文件归属、候选产物、评审和恢复证据。
记录不含凭据或私有研究内容。

待创建先登记唯一 dispatch key；`pending_creation` 的 clientThreadId 不能作为真实
threadId，也不能再次派发。API 返回真实 ID 后单独确认。API 错误或状态不明先查原操作
和对话，不自动重建。角色从 `docs/development/agent-coverage.json` 的 `roles[].id`
和 `stage` 读取。

外部 `create_thread` 前使用 `dispatch_reserve`，此时不填写 operation/client/thread
占位符；API 返回后用 `dispatch_record_result` 保存真实 operation/client 结果，再用
`dispatch_confirm` 绑定真实 thread ID。相同 key 的第二次 reserve 或结果重写都会失败，
错误/状态不明只进入检查状态，不自动重试。确认后可把真实专业 thread ID 写入 child
task 的 `professional_thread_id`。

任务必须经过依赖接受 → 运行 → 交付 → 独立审查 → 接受。execution 只能在角色最低
阶段满足时创建，design 可描述未来角色；阶段 5 execution 还需交易授权。审查必须绑定
任务指定的独立 reviewer，退回后保留候选历史并以新候选复验。取消请求只记录请求；确认
停止必须由执行者或带 `recovery_verified` 的恢复证据完成，之后才可释放文件归属。路径
按祖先/后代关系检查共享冲突。

阶段限制使用角色阶段表：design 模式可在阶段 0 定义未来角色；execution 模式必须满足阶段与额外授权，阶段 5 交易另行授权。冻结的盘前稿保留原快照/截止/摘要，盘后新增版本不能回填；方法、策略、程序、引擎、实验与有效性评估各自归属。

发布锁绑定 `task_id`、PM、已通过独立审查的 `candidate_id`、任务基线 SHA、最新
`origin/main` SHA、远端 VERSION 和下一 patch。取得锁前核对基线是远端祖先；占用者即使
很久无响应也不能按超时抢占。恢复先提供持有者状态和远端 Git/Actions/标签/Release/通知
六类证据；任何歧义都保持锁。第二 PM 必须重新读取最新 main 并重新集成复验。

发布顺序是：PM 先 fetch 最新 `origin/main`，完成集成并让独立审查通过源候选；再取得
串行锁。`acquire_lock` 会再次读取最新 main，要求任务基线等于该 SHA、候选包含该 SHA
且有集成验证证据；main 在此期间前进则拒锁，必须重新集成、生成新候选并复审。锁定后
只允许准备版本材料和最终发布提交，不把版本材料改动伪装成源候选复用。
先锁定已集成且独立验收通过的源候选；再按锁定的 `version` 准备
`VERSION` 与说明，运行 `release.py check`，提交最终发布材料并取得 exact SHA；最后由
工作流发布并保存 receipt。receipt 同时关联 `source_candidate`、发布 SHA、Actions、
Release 和通知结果。锁中的源候选不是随后版本材料的 SHA；持锁后源实现若发生变化，
原验收立即失效，必须产生新候选、重新独立验收并重新绑定锁。

锁记录 `source_candidate_sha`（已审查源候选）和可选的
`final_publish_sha`/`final_publish_version`（版本材料提交）。准备最终提交后必须调用
`publish-lock-bind-final` 显式绑定两者；绑定前的恢复证据 `exact_sha` 必须等于源候选，
绑定后则必须等于最终发布 SHA，且两种情况都必须带同一锁定版本、候选 SHA 以及远端
Git/标签/Release/通知的结构化结果。这样不会把 `base_sha`（锁定时的上一版
`origin/main`）误当成已发布提交。Windows 遗留短锁只通过 `OpenProcess` 的只读句柄、
`GetExitCodeProcess` 和显式 `argtypes`/`restype` 查询；句柄或退出码查询失败时保持锁，
不使用 `os.kill` 或超时抢占。

持锁后 fetch origin/main，从远端 VERSION 计算下一 patch；推送必须快进。失败恢复沿用
同 SHA/版本，不 force push，不修改历史发布材料。最终收据留本地或 Actions，不追加成功提交。

首版检查入口：

```text
python .agents/skills/multi-dialogue-development/scripts/orchestration.py show
python -m unittest tests/test_orchestration.py
git diff --check
```

CLI 还提供 `task-freeze`、`task-post-freeze-version`、`task-deliver`、`task-review`、
`task-accept`、`task-cancel`、`task-stop`、`task-release-files`、`publish-lock-recover`、
`publish-lock-bind-final` 和 `mutex-recover`；`task-create` 可带 parent、baseline、
worktree、branch、contributors、authors 与 versions。命令只更新本地协作状态，不代替
Codex 对话 API、GitHub Actions 或发布工具。
