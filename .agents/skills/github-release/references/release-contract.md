# 发布契约

- VERSION 使用无前导零的三段整数；默认首次 0.1.0，此后末位 +1。中间段、主版本及非连续调整必须有明确用户指令和 reason。按整数比较版本。
- `docs/releases/<version>.md` 是规范中文正文；同名 JSON 记录 version、previous_version、change（initial/patch/explicit）、reason、repository。CHANGELOG 保存版本摘要和说明链接。
- 标签 `v<version>`，标题 `XXStock <version>`。0.x 必须 prerelease 且 make_latest=false；稳定主版本只能用户明确开启。
- 比较链接为上次标签到本次标签；首次使用本次标签的提交历史链接。
- prepare 仅操作本地文件，不提交、不推送、不写远端，已有材料不覆盖。check 校验版本、来源版本、说明、索引；主线使用 push.before，遗漏升版失败。
- publish 只接受 GitHub Actions 的 push/main、匹配 event.after 的干净 HEAD 和指定仓库；标签始终指向这次 SHA。前一版本必须已发布且位于本次历史中。非快进主线停止发布，所有历史版本说明与元数据不可修改或删除。
- 同名标签必须指向目标 SHA；同名 Release 的标签、标题、正文、draft 和 prerelease 必须一致，否则停止。已成功部分可重跑恢复，不重写已发布内容。
- 创建 Release 后直接发送 #19 提醒，避免依赖 GITHUB_TOKEN 创建事件再次触发。仅成功创建／核验 Release 后才通知；缺配置或通知失败使 Actions 失败。网络请求无自动重试，保留人工重跑的重复可能性。
- 用户授权推送与发布后才能执行。自动选择 Skill 不是授权。秘密和运行状态存本地忽略目录或部署 secrets，不存 Skill；公共资产只含代码、文档、空示例及合成测试数据。
