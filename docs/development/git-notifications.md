# Git 与发布通知到 VChat / VoceChat 频道

状态：Git push 通知此前已真实验收；本轮加入正式 main 发布最终通知，外部验收见 [S0-009 交接](handoffs/skill-releases.md)。工具不依赖旧项目运行时、行情、数据库或产品 Agent。当前频道默认 **#19**，其他部署可修改频道与机器人。

## 触发与消息

| 事件 | 工作流与消息 | 不代表的能力 |
| --- | --- | --- |
| 正式 main push | [verify-docs](../../.github/workflows/verify-docs.yml) 先验证、发布，再发一次最终结果 | 不表示业务应用已经部署 |
| 开发分支 push | [独立通知](../../.github/workflows/notify-vocechat.yml) 报告 Git 推送 | 不表示测试通过或正式发布 |
| 非发布标签 push | 独立通知报告标签操作 | 不创建正式 Release |
| `v<version>` 发布标签 | 不额外发 push 通知 | 最终结果已由 main 发布链负责 |
| 手动通知验证 | 标记“非 Git 推送”的链路检查 | 不发布版本 |

main push 从独立通知中排除，避免早于校验的消息与发布最终消息重复。版本策略及 exact SHA 规则见 [发布规范](releases.md)。无变更的 `git push` 不产生事件；推送多个开发 ref 仍可产生多个事件，不以本地命令次数计数。

开发 push 消息含仓库、分支/标签、操作、推送者、提交短标识、至多五条提交标题、Git 变更和通知运行链接。正式发布消息含版本、exact SHA、校验/发布结果及可用的 Release/Actions 链接；失败时明确失败阶段，不假称发布成功。不发送提交正文、文件diff、环境配置或机器人地址/密钥。标题转义 Markdown、屏蔽提醒标记，并对已知密钥模式及当前机器人秘密脱敏。

手动触发 `workflow_dispatch` 用于链路验证，消息明确标为“非 Git 推送”。Actions 对极大量同时更新 ref 等场景存在平台限制，适用边界以 [GitHub push 事件说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#push) 为准。

## 仓库配置

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 配置：

| 位置 | 名称 | 值与默认 |
| --- | --- | --- |
| Secret | `VOCECHAT_BASE_URL` | 用户自己的 HTTPS 服务地址，公开模板为空 |
| Secret | `VOCECHAT_API_KEY` | 机器人密钥，公开模板为空 |
| Variable | `VOCECHAT_ENABLED` | `true` 启用；未配置时工作流跳过 |
| Variable | `VOCECHAT_GROUP_ID` | 默认 `19`，可改为自己的正整数频道 ID |
| Variable | `VOCECHAT_API_PREFIX` | 默认 `/api/bot` |
| Variable | `VOCECHAT_TIMEOUT_SECONDS` | 默认 `15`，允许 1～120 秒 |

机器人必须已加入目标频道。只复用 3.0 的地址与机器人身份，不更改 3.0 的频道、定时计划或配置。实际秘密由加密 Secrets 接收，不上传旧配置文件；本地工具也不 import 旧应用。

公开仓库的 fork 不携带原仓库 Secrets；使用者填写自己的配置后才能启用通知。通知 job 不在 PR 中注入机器人密钥，仅有 `contents: read`；同一发布工作流的 release job 单独拥有 `contents: write`。关闭时把 `VOCECHAT_ENABLED` 改成 `false`，无需修改代码。

## 本地配置与检查

本地 `scripts/vocechat_notify.py` 读取 `.env` 的 `VOCECHAT_*` 字段，进程环境优先；普通默认项来自 `config/config.example.json`，可在已忽略的 `config/config.local.json` 下 `notifications.vocechat` 覆盖。密钥只能来自环境或 `VOCECHAT_API_KEY_FILE`，不能写入 JSON；直接值与 `_FILE` 同时设置报冲突。

公开模板 [.env.example](../../.env.example) 默认为关闭，地址与密钥为空。用户自行创建忽略的 `.env` 并填写自己的值；本项目本机配置保留在本地，不随 Git 推送。普通配置可用：

```json
{
  "notifications": {
    "vocechat": {
      "enabled": true,
      "group_id": "19",
      "api_prefix": "/api/bot",
      "timeout_seconds": 15
    }
  }
}
```

检查配置，不发消息：

```text
python scripts/vocechat_notify.py --check-config
```

输出只含启用状态、地址/密钥是否已配置、频道、超时和缺失项，不回显地址、密钥片段或秘密文件路径。使用合成 GitHub push JSON 时可传 `--event-file <path> --dry-run` 预览，不会访问机器人；私有预览文件放 `.local/`。

## 发送与故障

依据 [VoceChat 官方 Bot 文档](https://doc.voce.chat/bot/bot-and-webhook)，请求为 `POST /api/bot/send_to_group/{gid}`，`x-api-key` 认证，`Content-Type: text/markdown`，正文是原始 Markdown。HTTPS 保持证书验证；禁止带用户名、密码、查询参数的服务地址，禁止重定向转发认证头。

成功日志只输出 `sent`、频道和 HTTP 状态。错误只输出安全分类/HTTP 状态，不回显上游正文、地址、请求或原始异常。401/403 检查机器人密钥和频道成员权限；404 检查频道 ID 与前缀；网络超时检查服务从 GitHub runner 是否可达。

通知失败使对应通知 job 失败，不回滚已成功的 Git 推送或 Release。不自动重试超时，因为该接口没有幂等键，服务器可能已经收到了消息。人工重跑可能重复投递，应先核对频道与运行结果；不会声称 exactly-once。正式发布重跑核验并复用已有版本，不升级 VERSION、不覆盖冲突 Release。正常工作流只发送一次最终结果，不逐阶段发送消息。

机器人服务必须能被 GitHub runner 访问；仅本机或局域网服务需要自行选用可达的 runner。独立研究网页的本机访问约束与此通知通道不同。

## 验证与维护

```text
python -m unittest discover -s tests -p 'test_*.py'
python scripts/verify_repository.py
git diff --check
```

合成测试覆盖配置优先级、秘密文件冲突、脱敏、真实 Bot 请求格式、频道、分支/标签、提交边界、错误正文不泄露、重定向拒绝与超时不盲目重试。真实发送以对应 Actions 与安全发送结果为验收，不在单元测试中调用实际频道。正式发布同时核对确切 SHA、标签、Release 属性与最终通知；未跑工作流时只记录本地通过。发布后不为成功结果新增提交或推送。
