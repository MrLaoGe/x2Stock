# Windows 空白 UI 架构测量证据

日期2026-10-08；独立QA只测精确x2Stock 5554d196旧preview作为技术证据，不替代最终带更新器/LFS项目树验收。原始测量保存在被忽略本地`E:/XXStock/.local/artifacts/windows-preview/architecture-qa/electron-5554d196-warm.json`及MEASUREMENT.md；公开表格无真实用户或provider数据。

## 观察与协议

Windows 11 Pro 10.0.26200 x64；Ryzen9 9950X，16核32逻辑线程，RAM100,556,521,472B约93.65GiB，DPR1.5；Electron44.7.0。相同React空工作台已运行过，三个样本全部记warm，未flush缓存/冷启。direct child_process.spawn前monotonic起计，到CDP发现精确app.asar页面且root正文非空止，50ms轮询；含调试端口发现开销，不是first paint。DNS屏蔽，独立端口；每次关闭自己的测试窗口，偏好不变。

| 暖启动样本 | readiness ms | 空闲全树WS MiB | 30次交互后WS MiB | 约5秒交互CPU累计增量 s | 全32核容量比例 |
| --- | --- | --- | --- | --- | --- |
| 1 | 1095.98 | 324.61 | 371.82 | 0.78125 | 0.485% |
| 2 | 238.55 | 323.52 | 372.10 | 0.81250 | 0.503% |
| 3 | 222.79 | 338.42 | 386.04 | 1.03125 | 0.646% |

**Derived** readiness中位238.55ms。空闲测量窗6.10–6.24s累计CPU增量均在计时分辨率下为0，不表示绝对零CPU。交互是30次导航→Save→Reset→返回，窗长4.99–5.05s，非业务性能或峰值。全树包括renderer/GPU/network及所有后代，第三次额外无--type helper也计入；不能把该helper误叫第二browser。

WS求和含共享页重复计数，不叫独占RAM；PrivateBytes与CPU原始字段在local evidence，多个process snapshot有采样开销且非同时原子。未测峰值、硬盘冷读、长任务、多显示器、物理Windows/文字缩放。旧ZIP158,298,900B，完整展开385,691,644B/72files，EXE246,302,208B；这是已完整资源，不是只拿核心exe比较。最新人类发行要求是源码树随附runtime，旧ZIP数只作为技术测量。

## Tauri与选择

**Observed** PATH无cargo/rustc/rustup/cl/link/cmake/ninja/msbuild，默认.cargo/bin及标准VS/SDK Include未发现；系统有WebView2 153.0.4234.48和154.0.4258.62目录。没有为评估安装巨大环境或改系统。**Unknown** Tauri2相同React构建启动/全树CPU/内存/完整runtime分发体积，不能据官网或系统WebView存在编造实测。

**Decision** 当前Electron是已证明可无需外部runtime打开本地UI的选择；不宣称性能更优。它较大，需要LFS及archive设置/配额验证。将来若同UI Tauri完整runtime可构建，按同协议加冷/暖与真实分发包测量后再评估换壳。证据边界与业务存储选择见[架构](../architecture.md)。
