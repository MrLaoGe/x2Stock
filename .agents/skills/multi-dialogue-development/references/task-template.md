# 派发与交接模板

## 派发

- 任务 ID、父任务、老板/PM/执行对话真实 ID；异步创建 operation/client ID 单独存储。
- 人类授权来源与范围、角色、当前阶段、design/execution 模式、禁止范围。
- 业务专责、实现责任、指定独立验收角色与人员/对话；实现者不能验收自己。
- 依赖任务及接受证据；worktree、分支、基线 SHA；独占文件/共享路径所有者。
- 输入、需求、具体产物、可观察验收；snapshot_id、as_of/cutoff、方法/策略/代码/数据版本（不适用显式写明）。
- 失败、缺数据、冲突：保留证据并报告 PM；缺失不补造，阻断依赖不执行。

## 返回

- 状态、局部提交、文件与产物引用、检查命令和证据；残余缺口。
- 审查结论 passed/returned/insufficient，审查对话、候选 SHA、返工要求与复验。
- 取消分开记录 requested/confirmed_stopped；确认前保留所有权和运行资源。
- 发布由 PM 汇总：基线协调、版本、exact SHA、Actions、Release、通知分别验收。
