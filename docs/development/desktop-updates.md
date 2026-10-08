# Windows 整项目分发与更新验收

状态：工程集成与本地验收进行中，最终候选及独立收据见[UI-001交接](handoffs/frontend-style.md)。Include LFS、实际远端source archive和真实Release更新仍为外部未验证；本地合成成功不能替代这些结果。

## 启动和公开资源

用户下载整个项目，由根`启动.bat`相对启动`desktop-runtime/win-x64/x2Stock.exe`。BAT不安装依赖、构建或下载；其UTF-8/CRLF原始字节通过根`.gitattributes`的`-text`保存，避免GitHub归档还原LF后被CMD错误解析。校验绑定规范完整字节，不能只用路径子串或命令黑名单证明离线。

资源清单唯一维护于[runtime-files.json](../../desktop/updater/runtime-files.json)，Python公开资产/归档门槛与桌面解压器共享73项EXE/DLL/pak/locale/asar/清单/许可证。缺任一资源、额外文件、LFS指针、摘要或x64 PE不符均拒绝；其他目录的编译文件和私有配置仍不可提交。程序生成的`.recovery`和`.x2stock-*`只在安装目录本地用于事务恢复，不随公开项目发布。

GitHub源码归档默认只含LFS指针。管理员须开启Archives include LFS，并在最终main exact SHA真正下载验证；没有可用归档时工作流停止在验证阶段，不发布更新元数据或通知成功。旧standalone EXE ZIP留审计，不再每个正式版本另做ZIP。

## 两层版本绑定

根VERSION是正式版本唯一事实源。`resources/build-manifest.json`恰有7字段：`schema`、`repository`、`version`、`build_source_sha`、`source_tree_hash`、`platform`、`arch`。build SHA为构建时已存在的源码提交，不是之后二进制提交的自指SHA；本地验证要求它是HEAD祖先。

source tree hash对Git跟踪的`frontend/`、`desktop/`、`VERSION`计算，排除node_modules、dist、release、renderer、build、Python缓存和构建缓存；相对POSIX路径按UTF-8字节排序，对每文件生成`摘要 + 两个空格 + 路径 + 换行`再整体SHA-256。归档单独重算相同源码身份，确保root VERSION与renderer/desktop源码匹配；不声称独立签名或可复现编译。

同Release只允许一个`x2Stock-<version>-update.json`资产，最多16KiB，恰有9字段：

| 字段 | 约束 |
| --- | --- |
| schema / repository / version | schema=1、MrLaoGe/x2Stock、root VERSION与v标签一致 |
| source_sha | 最终标签解析到的40位exact commit，不用branch或preview父SHA |
| source_tree_hash | 与runtime manifest及归档独立重算结果一致 |
| archive_url | 固定GitHub codeload该仓库/exact commit的zip地址 |
| archive_sha256 / archive_size | 本次真实归档下载的SHA-256与准确字节数；至多512MiB |
| runtime_subdir | 固定desktop-runtime/win-x64 |

客户端先核对GitHub API返回的metadata资产digest，再核对下载archive的digest/size。相同版本资产只在字节摘要一致时复用；冲突、重复、缺digest不覆盖、不删除、不盲重试。GitHub/TLS/仓库权限是当前信任根，独立签名未实现；GitHub未来改变归档压缩字节时摘要校验会失败，不能跳过检查。

## 本地与远端门槛

Python合成测试、前端类型/风格/行为/构建、Node桌面行为、materialized LFS资源及BAT实际启动分开记录。BAT烟测复制资源到OS temp中带nonce marker的`x2stock-fixture-*`，使用独立AppData/单实例领域，只关闭自己精确可执行路径的进程。CDP确认固定本地asar页面、非空root、默认zh-CN、bridge、title、实际DNS阻断参数及新profile；窗口响应不算通过。

正式main工作流：公开仓库/版本验证及Windows LFS验证 → 实际下载GITHUB_SHA源码归档并校验/解压 → 从下载内容的根BAT离线启动 → 保存唯一metadata artifact → 旧release helper创建/复用exact SHA Release → 新metadata publisher上传/复验唯一资产 → 一次既有VoceChat最终通知。main与发布标签不额外发push通知。

A汇集A/B/C候选，准备最终VERSION后须重新构建runtime、暂存LFS对象、复验source hash，并让独立审查绑定最终SHA。C不预占版本、不自行推送。远端待验保留external_unverified，最终只以Actions、Git、Release及#19结果报告，不补成功记录提交。

## 替换与恢复

启动后仅检查Release，6小时基础间隔并离线退避，用户确认已检查的releaseId/version才下载与应用。renderer没有任意URL、路径、token或文件操作接口。raw ASAR处理使用Electron original-fs，不能把Electron patched fs对asar目录的视图误当真实文件。

staging/hash/manifest通过后准备同卷next、旧版backup及固定`.recovery`完整副本。helper等旧进程退出、再次验证后逐次rename，使用有界重试应对短暂Chromium文件占用；两次rename并非整体原子事务。新程序须交回nonce/PID/version/tree及非空renderer健康确认，否则恢复旧资源。pending/journal与固定恢复入口跨越“旧目录已移走但新目录未到位”缺口；根BAT在主EXE缺失时相对启动`.recovery/x2Stock.exe --x2stock-recover`，恢复模式在profile/单实例前检查受限marker与摘要，不信任任意目标路径。

验收须包括真实healthy、空renderer回退、两次rename之间/之后中断再从BAT恢复，并检查profile/研究资产未改；直接调用recoverSwap函数的合成测试不能替代这些进程证据。网络/校验/权限错误保持旧资源，未来业务模块仍不扩张。
