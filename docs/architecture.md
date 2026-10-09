# Windows 桌面架构

当前产品入口是 Windows x64 `启动.bat` → `desktop-runtime/win-x64/x2Stock.exe`；浏览器只用于开发与视觉调试。React 空工作台和三语首包已本地独立验收；项目树随附 runtime、Git LFS 归档和更新闭环。无金融业务、数据库、Python 服务或旧数据导入。当前采用单用户桌面部署，服务器方案留待后续模块。

## 当前与后续技术职责

| 层 | 当前选择 | 实施状态及边界 |
| --- | --- | --- |
| 用户入口 | 整个源码项目包含完整 Windows runtime，根 BAT 相对启动 | 禁止 BAT 临时下载或 npm 构建；远端源码归档真实二进制待验 |
| 桌面壳 | Electron 44.7.0 x64；内置 Chromium/Node 仅主进程可用 | contextIsolation、sandbox、renderer Node关闭；无安装器/外置 runtime要求 |
| 界面 | React/TypeScript/Vite 与 Hash 路由 | 本地 file资源，Vite base './'；canonical token/组件；三语本地词典 |
| 更新 | 固定 MrLaoGe/x2Stock Release、受限 IPC、受信整项目归档 | 仅切换 desktop-runtime/win-x64 全部资源，用户确认，hash/安全解压/回退/renderer健康门槛；验收未闭合 |
| Python 生态 | FastAPI/Pydantic/SQLAlchemy/Alembic；按模块启用的后台进程 | 首包不启动；打包解释器随启用模块提供，不要求使用者安装 Python |
| 单用户事务存储 | SQLite WAL，归属与显式 Alembic保留 | 设计，未创建业务表；事实、任务、用户研究与来源关系由模块决定 |
| 批量分析 | Parquet + DuckDB，单后台进程持有嵌入式写入 | 设计；不先搬旧库或造全数据平台 |
| 服务器 | PostgreSQL、Docker Compose、认证与多用户隔离 | 后续独立部署方案；不是桌面启动条件，不同时开发两套后端 |

Ant Design/TanStack Query/ECharts 仅在已选模块需要时引入；大表用分页/虚拟化、图表按需加载、计算留后台，不能在本轮用虚构行情堆首屏。业务来源仅三类准入适配器；React或产品研究Agent不能直接获取provider数据，普通查询不暗中付费AI或采集。

## 选择 Electron 的证据与限制

**Observed**：Electron 空白 UI 构建具备完整本机运行资源，已验证中文空格路径、非空本地 renderer 与三语首包。当前不以此宣称 Electron 与其他桌面壳的性能优劣；性能数据和研发测量记录属于内盒。

Electron满足现阶段无额外安装和渲染一致性；代价是386MB级完整运行目录与246MB核心EXE，必须LFS管理。不能据现有结果宣布Electron比Tauri快或节省内存。Tauri依赖Windows WebView2；官方描述fixed runtime约增加180MB，系统runtime模式仍是外部先决条件。未来若工具链和运行条件允许，应对同一UI比较完整资源/全进程/暖冷启动，再决定是否换壳。[Tauri Windows发行](https://v2.tauri.app/distribute/windows-installer/)、[Electron性能指南](https://www.electronjs.org/docs/latest/tutorial/performance)。

## 分发、版本与用户资料

用户下载整个公开项目；`desktop-runtime/win-x64`包含EXE、DLL、locale、app.asar、构建清单与Electron/Chromium许可证，不能只复制EXE。该目录严格白名单并通过Git LFS跟踪；其他exe、数据库、用户配置、provider文件不能藉此进入公开仓库。GitHub源码归档默认含LFS指针，需要管理员开启Archives include LFS，再实际下载确认PE二进制/完整资源/BAT离线启动；本地复制不算远端通过。[GitHub LFS归档规则](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository)。

root VERSION是正式版本事实源。runtime清单记录version、build_source_sha、source_tree_hash、repository、win32/x64；编译二进制提交不能嵌入它自身的最终SHA，因此发布清单绑定最终tag/exact SHA并验证源码treehash与runtime一致，不用预览parent SHA冒充tag SHA。treehash对Git index tracked frontend/desktop/VERSION的canonical blob字节计算，排除构建中间产物，按相对POSIX路径排序每文件sha256再整体sha256；不用checkout CRLF字节，避免与archive LF不一致，真实源码修改需重新提交构建。

普通新安装使用APPDATA/x2Stock；已有APPDATA/XXStock profile/session则安全复用，不复制live LevelDB、不删旧目录。新语言key优先，缺失才兼容读旧key。程序/resources、更新缓存、用户资料分开；真实物理E:/XXStock/worktree保留，旧ZIP只是审计。旧名与新名进程不能同时占同一profile。只读/保护目录的更新必须拒绝并继续打开旧程序，不能要求管理员绕过权限。

## 更新边界与失败恢复

Electron内置autoUpdater描述的是已安装Squirrel/MSIX形态，不能假设其支持源码树portable；本产品使用独立受限更新机制。[Electron autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater/)。

主进程从固定公开repo读取Release，按整数SemVer筛选更高版本、draft=false、0.x prerelease=true，文档-only版本没有受信更新清单则跳过。启动后非阻塞自动检查、合理间隔及手动检查均不得下载执行；可用更新展示版本/说明/大小并需明确确认。renderer只发送checked releaseId/version/confirmed，不能提供URL、路径、token。API HTTPS+repo控制+GitHub digest是当前真实性信任根，独立发布者签名未实现；仓库账号被攻陷仍会损害信任，不能把SHA完整性宣称独立签名。

同Release受信JSON清单绑定final tag SHA、整项目codeload URL、archive大小与SHA、runtime路径及source_tree_hash。下载与解压有超时/限额，拒绝路径穿越、ADS、设备名、大小写冲突、符号链接、CRC错误和架构/版本/源码身份不符。只提取runtime到独立staging，再准备目标同卷sibling；源码/.git/.env/.local/AppData不参与替换。

更新辅助进程独立于 renderer，并在用户确认后校验完整运行时、版本和回退状态。网络、校验或权限错误保持旧程序，不删除资料或声称已更新；详细实现随公开更新协议和后续版本逐步验收。

## 未来 Python 生命周期与接口

只有用户选定模块需要金融计算/采集时，Electron主进程启动随包Python onedir服务；未启用模块不预装业务服务、worker或数据库。单实例管理进程，退出时先停止新任务、让事务/lease收尾，在有界超时后终止自己的后台，不杀其他系统进程。采用PyInstaller onedir以避免onefile每次启动解包；包必须在目标Windows构建并验解释器/依赖许可。[PyInstaller运行模式](https://pyinstaller.org/en/stable/operating-mode.html)。

FastAPI作为内部业务边界保留，但默认只监听127.0.0.1系统分配端口。随机每会话凭据由主进程通过stdin交给自有后台，状态端口经独立管道返回；主进程代理有限领域IPC，不把地址/凭据/任意请求工具暴露renderer。backend身份固定local/local并按user/workspace过滤；读取不能暗中采集或AI。长任务返回taskId由独立任务组件跟踪，后台计算不阻塞界面主线程。token/动态端口/生命周期/跨归属需模块行为测试，当前这些服务未实现。

## SQLite与分析数据约束

SQLite WAL是本机单用户候选，不是无迁移。一个业务后台持有写入职责；短事务、显式Alembic、唯一键幂等、bounded busy retry，失败保留已有有效数据。使用checkpoint水位监控，长读查询避免无限保持WAL；备份用online backup或停写checkpoint后成组快照，不能单独复制主db遗漏WAL。恢复须验证用户资产引用、schema版本及任务lease；原始文件由数据库登记hash和来源，缺失保持缺失。

SQLite官方当前披露WAL-reset修复3.51.3及回补3.44.6/3.50.7，最终模块要核验实际bundled sqlite3.sqlite_version与补丁，不能只看Python版本；本轮没有运行数据库。[SQLite WAL](https://www.sqlite.org/wal.html)。DuckDB嵌入式读写由同一个后台持有，多读副本/Parquet用于分析；不让API/worker跨进程同时写。Quack beta不引入当前范围，Parquet是可重建数据集而非未经登记第二事实源。[DuckDB并发](https://duckdb.org/docs/current/connect/concurrency.html)。

未来任务仍携带user/workspace、lease generation/fencing token，过期执行者不能发布结果；来源/时点/计算/AI分层，交易日历和Asia/Shanghai不由语言变更。远程/多用户需先认证与隔离，不能仅放开bind。默认不迁移；评估血缘/质量不是授权导入，按用户选定模块另批处理。
