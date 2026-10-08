---
name: github-release
description: "发布 x2Stock 正式 main 更新或恢复失败的发布：整理中文说明、递增版本、验证公开资产、提交推送、创建 GitHub Release 并通知 VoceChat。普通开发分支提交无需此 Skill；自动发现不授予远端写入权限。"
---

# GitHub 版本发布

执行前阅读根目录 AGENTS.md、任务台账、VERSION、CHANGELOG.md 和 [发布契约](references/release-contract.md)。先核对用户是否授权本批推送与发布；已有授权继续执行，不重复询问。未授权时完成本地准备与验证后再请求推送授权。

1. 核对 origin、远端标签、上次 Release 和 Actions。前次发布未完成时先恢复同一提交，禁止为失败恢复另升版本。
2. 从实际差异整理中文说明：概述、适用的新增功能／优化改进／问题修复／兼容与升级说明、验证结果。省略空分类，不宣称尚未验证的远端结果。
3. 将说明草稿放入被忽略的 `.local/`，运行 `python .agents/skills/github-release/scripts/release.py prepare --notes-file .local/release-notes.md`。首次为 0.1.0，默认只递增末位。用户明确要求其他版本时使用 `--version X.Y.Z --allow-version-change --reason "用户指定的版本调整"`；不得自己授权大版本升级。
4. 运行 `python .agents/skills/github-release/scripts/release.py check`、`python scripts/verify_repository.py`、`python -m unittest discover -s tests -p "test_*.py"` 和 `git diff --check`。审查 Skill frontmatter、登记、引用及权限边界；正式发布前由独立 Agent 审查发布场景。检查暂存内容，排除凭据、真实数据和个人资产。
5. 经授权提交本批文件并推送 main。提交说明包括版本和实际变更，推荐 `x2Stock 0.1.0 建立项目 Skill 与版本发布流程`。开发分支和非发布标签沿用普通推送通知，不升版。
6. 主线工作流验证本次确切 SHA，运行 helper 的 `publish`，创建／复用标签和 Release，然后在同一工作流复用 VoceChat 客户端发送最终提醒。不要本地绕过守卫执行 publish，不要再手动补发 push 提醒。
7. 核验 Release 正文、预发布状态、标签 SHA 与 Actions 通知结果，交接输出版本、提交、链接、测试及遗留问题。成功凭据记录在 Actions 或忽略的本地收据；不得为补写发布成功另造版本。

失败时先定位阶段：Git 已推送则重跑原提交；Release 已成功则复用它；通知超时不自动重试。人工重跑可能重复通知，消息保留运行 ID 和 attempt。已有标签 SHA 或 Release 正文冲突必须停止并报告，不能删除、移动或覆盖。
