# 版本与正式发布

本规范用于已授权的 `main` 发布批次。当前发布机制的本地交付与真实 Actions 验收分别记录于 [任务台账](task-ledger.md) 和 [本轮交接](handoffs/skill-releases.md)，不能把本地测试通过写成远端发布成功。

## 版本材料

- 根目录 [VERSION](../../VERSION) 是当前版本的唯一事实源，格式为 `X.Y.Z`。首次从 `0.1.0` 开始；已有版本时，每批正式发布默认 patch 加一，一批可包含多个提交。
- 只有用户明确指定版本级别或目标版本时，才改变 minor/major。显式版本需使用 `--version` 与 `--allow-version-change`，不能根据 Agent 对变更大小的判断自行升级。
- [CHANGELOG.md](../../CHANGELOG.md) 保存发布索引，由准备工具维护；正式说明存于 `docs/releases/<version>.md`，首行标题为 `# XXStock <version>`。说明写变化、验证与实际限制，不写虚构的业务能力。
- Git 标签为 `v<version>`，GitHub Release 名称为 `XXStock <version>`。`0.x` 发布设为 prerelease 且不标为 latest；它发布设计/运维成果，不表示业务应用可用。

## 准备与检查

先写好本批说明，再准备本地材料：

```text
python .agents/skills/github-release/scripts/release.py prepare --notes-file <已写好说明文件>
python .agents/skills/github-release/scripts/release.py check
python scripts/verify_repository.py
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

`prepare` 只修改本地 VERSION、CHANGELOG 和版本说明，不创建远端标签或 Release。无 VERSION 时生成 `0.1.0`；已有 VERSION 时默认准备下一 patch。明确的版本变更使用：

```text
python .agents/skills/github-release/scripts/release.py prepare --version X.Y.Z --allow-version-change --reason "用户明确指定的版本调整" --notes-file <已写好说明文件>
python .agents/skills/github-release/scripts/release.py check --base-sha <已确认的父版本提交>
```

`check` 检查本地材料、父版本关系和说明一致性；`--base-sha` 明确比较基准。正式集成前，主 Agent 核对版本、说明、全部变更、评审与实际测试，再提交并推送已授权批次。未跟踪或工作区中尚未提交的材料不会被 GitHub 发布。

准备新批次和失败恢复是两件事。当前批次已提交而 Actions 失败时，不再次运行默认 `prepare`，否则会产生新版本。重跑已有工作流应使用同一 SHA、版本、标签和说明。

## GitHub Actions 发布链

[verify-docs](../../.github/workflows/verify-docs.yml) 在同一工作流内依次完成验证、发布和最终通知。发布只处理仓库正式 `main` 的 push，`publish` 要求 Actions token 与该事件的 exact `GITHUB_SHA`；普通本地终端、PR、开发分支和手动验证不承担远端发布。

1. 校验公开资产、发布材料、行为测试和提交差异。
2. release job 以 `contents: write` 将 `v<version>` 指向本次验证的确切 SHA，再创建对应 GitHub Release。
3. 同一 release job 的后续通知步骤使用机器人 Secrets 向配置频道发送本次最终结果，默认 #19；GitHub 写入令牌仅注入发布步骤，通知步骤不注入该令牌，checkout 不持久保存凭据。消息包含版本、摘要、Release、比较链接和运行标识；投递结果单独记录在 Actions。

通知不能只写“Git 已推送”却让读者误以为发布成功。正式 main push 不再触发另一路独立 push 通知；发布标签也不重复通知。不依赖 `release` 事件唤醒另一工作流，避免权限令牌创建事件的触发差异与竞态。开发分支、非发布标签仍沿用 [Git push 通知](git-notifications.md)。

## 冲突、失败和重跑

| 情况 | 行为 |
| --- | --- |
| 标签/Release 尚不存在 | 为验证的 exact SHA 创建当前版本 |
| 同版本标签与 Release 已正确存在 | 核对 SHA、说明、名称与发布属性后复用，不额外创建 |
| 标签指向其他 SHA、Release 材料不一致 | 停止并报告冲突，不移动标签、不覆盖远端说明 |
| 标签创建成功而 Release 失败 | 重跑同次任务，核对标签后继续创建该版本，不升版 |
| 验证或发布失败 | 保存真实失败状态，当前版本不变；修复需要新提交时由主 Agent 处理 |
| Release 成功而通知失败 | 保留成功 Release，通知单独报告失败；不撤销发布、不为了通知升版 |
| 通知超时或结果不明确 | 先核对频道与 Actions，不盲目重发；Bot 接口不能保证 exactly-once |

“一次最终通知”表示一次正常工作流只发最终结果，不在校验、标签、Release 各阶段逐条发送。人工重跑可能再次产生消息，不能声称网络投递严格一次；应先判断已有投递，再选择需要重跑的失败部分。

发布验收通过 Actions 与用户可见输出记录，不为写一条“发布成功”再提交并推送，避免触发下一版本和通知循环。台账和交接应在推送前如实填写本地结果、待外部验收项；推送后在对话中报告可验证 Release/Actions 链接和最终状态。
