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

持锁后 fetch origin/main，从远端 VERSION 计算下一 patch；推送必须快进。失败恢复沿用
同 SHA/版本，不 force push，不修改历史发布材料。最终收据留本地或 Actions，不追加成功提交。

首版检查入口：

```text
python .agents/skills/multi-dialogue-development/scripts/orchestration.py show
python -m unittest tests/test_orchestration.py
git diff --check
```
