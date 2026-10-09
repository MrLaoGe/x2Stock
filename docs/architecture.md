# 产品架构

当前产品采用 React/TypeScript 渲染层和 Electron Windows x64 桌面壳。完整运行资源随项目提供，根启动 BAT 仅相对启动本地 EXE。浏览器用于源码开发调试。

单用户金融后台仍为规划，后续按启用模块增加 SQLite WAL 和按需 Python 服务；当前没有金融 API、采集、数据库、迁移、研究或交易模块。源码与用户设置目录相互独立。
