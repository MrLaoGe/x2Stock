# 项目 Skill 与发布机制交接

任务：S0-009；日期：2026-10-08。用户批准项目 Skill 标准化、正式 main 批次版本与同工作流最终通知。本轮不开发 A 股业务代码，不移植旧 3.0 Skill 包，不读取或修改旧配置。

## 当前状态

| 能力 | 状态 | 产物与证据 |
| --- | --- | --- |
| Skill 目录与开发/业务分类规则 | 本地实现与校验通过 | [组织规范](../skills.md)；Skill 入口、注册表、UI元数据及引用已核验 |
| 版本、exact SHA、Release 与通知规则 | 本地实现与独立审查通过 | [发布规范](../releases.md)；版本与恢复测试使用临时合成仓库 |
| 文档与协作入口 | 本地文档完成 | README、AGENTS、贡献规范、索引、协作与通知说明 |
| 发布 helper、注册表、工作流和行为测试 | 本地实现与核验通过 | 43项测试、51个公开资产及Skill校验；工作流真实运行待推送 |
| 0.1.0 GitHub Release 与 #19 最终通知 | 外部验收待工作流 | 本地文档提交不创建 Release、不发机器人消息 |

## 关键交接

根 VERSION 为唯一版本源，首次 `0.1.0`，正式 main 每批默认 patch 加一；明确用户指定才允许 minor/major。版本说明与 CHANGELOG 必须与准备结果一起提交。`0.x` 为 prerelease 且非 latest。

`verify-docs` 先验证，再对 exact `GITHUB_SHA` 创建标签/Release，最后由同一工作流发送结果。main 和发布标签排除独立 push 通知，开发分支与其他标签保留 push 通知。Release 冲突不覆盖、失败重跑不升版、通知歧义不盲重试。

业务 Skill 不获得工具和交易权限，可执行逻辑仍由后端与 worker 实现。只使用新版独立目录及配置；注册表不收集用户资产或秘密。

## 推送前核验

- 完整集成后 `python -m unittest discover -s tests -p 'test_*.py'` 通过，共43项；覆盖版本、SHA、材料冲突、历史重写、恢复、标签路由、消息及秘密脱敏。
- `python scripts/verify_repository.py` 通过，共51个公开资产，原文档分支的缺失链接已全部消除。
- Skill creator 的 `quick_validate.py` 使用 `python -X utf8` 执行通过（Windows 默认编码需显式 UTF-8）；Skill UI元数据、登记与相对引用均通过检查。
- release helper 的 `check --base-sha` 使用已核对的远端main SHA通过；`git diff --check` 通过。VERSION为0.1.0，canonical notes与CHANGELOG已生成。
- 独立审查复现的问题已修复并定向复核：非版本v标签通知、已发布材料不可改写、非快进主线拒绝发布、UI UTF-8。GitHub协议异常只输出安全分类。
- GitHub只读预检确认尚无标签／Release，机器人Secrets已配置、启用且频道19。外部验收保持待本次工作流；推送后通过Actions与用户输出报告结果，不追加成功记录提交。

原批次下一轮入口为数据中心与迁移；当前已由 [ADR 0006](../../adr/0006-module-first-new-project.md) 调整为[最小应用骨架](../../modules/application-skeleton.md)，之后用户选业务模块，默认不迁移。发布工具与 Skill 治理属于阶段 0 开发运维，不证明任何业务模块已经实现。
