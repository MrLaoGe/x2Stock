# ADR 0002：模块化单体和独立部署

日期：2026-10-08；状态：accepted。

## 背景

旧项目为 React/TypeScript 与 FastAPI/Python，主要持久化是 SQLite/文件和分析 DuckDB。新版需要跨平台、长期存储、可迁移结构及用户边界。

## 决策

保留主要语言生态，前端引入常规路由、组件和查询状态层；后端模块化单体，PostgreSQL 为长期事实和业务记录的主存储，显式 Alembic 迁移，独立 worker 使用同一服务层。按需用 Parquet/DuckDB 做可重建的分析视图，不把它们作为第二套权威业务库。

Docker Compose 为部署基线，默认本机单用户；API/worker/PG 使用容器内部网络，不在首期引入 Redis、微服务或消息集群。个人资产携带 user/workspace 归属，多人上线前另做认证。

## 影响

部署者需要独立数据库与运行环境，接受比 SQLite 更多的基础依赖以换取一致的迁移和并发边界；当前开发不依赖这些服务，阶段 1 才实现和锁定版本。

详见 [架构](../architecture.md)、[配置](../configuration.md)。
