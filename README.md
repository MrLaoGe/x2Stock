<p align="center">
  <img src="docs/assets/readme-header.jpg" alt="项目趣图" width="270">
</p>

# x2Stock

x2Stock 是面向 A 股投资者的 Windows 免安装研究工作台。公开仓库提供可运行的桌面程序、产品源码、用户配置示例和公开接口契约；浏览器前端只用于开发调试。

> 本仓库是产品外盒。内部研发 Skill、任务编排、路线决策、设计留档和发布控制保存在私有仓库 `x2StockBox`，不会随公开产品分发。

## 当前状态

当前版本是 `0.1.1` 预发布，首包为三语空工作台（简体中文、繁體中文、English），尚未启用行情采集、数据库、研究 Agent、回测或交易功能。用户下载完整仓库后运行根目录的 `启动.bat`，不要只复制 `x2Stock.exe`。

## 快速开始

1. 安装 Git LFS 后克隆仓库，或下载包含 LFS 文件的完整源码归档。
2. 复制 `.env.example` 为本地 `.env`，只填写自己拥有的凭据。
3. 双击 `启动.bat`。

产品运行不依赖旧版 ReviewStock_Codex；用户数据和凭据保存在本机忽略目录，不会写入仓库。

## 项目交流群

- 私域交流群：[https://qq.mctop1.com/](https://qq.mctop1.com/)
- QQ交流群：1126775948

## 公开文档

- [桌面架构](docs/architecture.md)
- [配置说明](docs/configuration.md)
- [数据与接口契约](docs/contracts.md)
- [数据源能力](docs/data/sources.md)
- [文档索引](docs/README.md)
- [版本记录](CHANGELOG.md)
- [参与贡献](CONTRIBUTING.md)

## 本地校验

```text
python scripts/verify_repository.py
python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

校验器检查公开文件、相对链接、配置模板、运行时白名单和常见凭据模式，不会访问数据源或发送通知。

## 许可与数据

代码采用 [MIT](LICENSE)。数据源响应、新闻正文、个人研究资产和真实凭据不随项目发布；MIT 不代表第三方数据的再分发授权。
