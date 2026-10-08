# 参与 x2Stock

## 开始之前

当前仓库为业务设计与开发运维仓库，尚无 A 股业务应用。先阅读 [文档索引](docs/README.md)、[任务台账](docs/development/task-ledger.md) 和 [AGENTS.md](AGENTS.md)，确认任务所属阶段。首个实施模块是数据中心与迁移，不要求贡献者同时实现所有业务。

## 工作流程

1. 为模块任务建立独立分支；并行 Agent 使用独立 worktree。
2. 按 [交接模板](docs/development/handoff-template.md) 说明输入、输出、来源、兼容和验收范围。
3. 对影响公共契约或核心边界的变更先补充 ADR；其他任务直接实施用户已授权的修改。
4. 用合成 fixtures 验证行为，执行相关检查。
5. 更新任务台账、模块文档和交接记录，再提交可审查的变更。

PR 描述先说明触发问题与变化后的行为，再列验证结果和实际限制。简洁变更不需要长篇流程记录。

## Skill 与正式版本

新增项目 Skill 使用 `.agents/skills/<name>/SKILL.md` 并同步注册表，注明开发/业务分类、用途、状态及依赖；具体规则见 [Skill 组织](docs/development/skills.md)。未来业务 Skill 调用后端领域能力，不把提示词当权限控制，也不整包移植旧项目。

每批正式 main 发布先写说明，使用 [github-release](.agents/skills/github-release/SKILL.md) 的本地 `prepare/check`，再集成验证并提交。默认从 `0.1.0` 开始且每批 patch 加一；明确用户指定才改变 minor/major。版本材料不由 CI 临时补提交。发布权限和失败恢复见 [发布规范](docs/development/releases.md)。

开发分支推送不会创建正式 Release；其 push 通知只说明推送结果。正式 main 发布验证、标签、Release 与最终频道通知在同一工作流。已有 Release 冲突不覆盖，失败恢复保持原版本，发布后不为成功记录再推一次。

## 公开材料

不要提交 API 密钥、真实行情缓存、新闻正文、个人股票池、报告、交易记录、数据库或运行日志。旧项目的整个 Git 历史不合并进来；提取源码时登记原位置、改造内容和第三方许可。

数据源适配需要提供接口说明、字段口径、权限/频次核验和失败行为。前端不得直接请求第三方数据源。用户私有查询和后台任务都必须遵守归属边界。

## 本阶段验证

```text
python scripts/verify_repository.py
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

后续运行依赖、测试和构建命令随相应模块实现更新。目前不要把规划中的命令描述为已经可运行。
