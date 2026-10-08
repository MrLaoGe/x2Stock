# 项目 Skill 索引

规范根目录为 `.agents/skills/`，每个目录包含 SKILL.md，按需附带 scripts、references 和 agents/openai.yaml。机器可读登记见 [registry.json](registry.json)，管理规范见 [skills.md](../../docs/development/skills.md)。

| Skill | 分类 | 状态 | 用途 | 依赖 |
| --- | --- | --- | --- | --- |
| [github-release](github-release/SKILL.md) | development | active | 版本、中文说明、GitHub Release 与频道通知 | Git、Python 3.11、GitHub Actions、现有 VoceChat 客户端 |
| [multi-dialogue-development](multi-dialogue-development/SKILL.md) | development | active | 独立 PM、持久专业对话、任务状态、独立验收与发布协调 | Git、Python 3.11、Codex 对话工具、github-release |

业务 Skill 按模块逐个新增，业务代码遵循后端服务和数据访问架构。不得将秘密、运行数据或旧项目 Skill 整包放入本目录。
