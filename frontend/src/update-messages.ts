import type { UpdateError } from './update-contract'

type UpdateMessages = {
  errors: Record<UpdateError, string>
  updates: string; desktopOnly: string; check: string; refresh: string; install: string; close: string; cancel: string
  current: string; candidate: string; notes: string; noNotes: string; size: string; published: string
  confirmTitle: string; confirmBody: string; confirmInstall: string; checkFailed: string
  idle: string; checking: string; available: string; noUpdate: string; downloading: string
  verifying: string; staged: string; applying: string; error: string; unknownVersion: string
}

export const updateMessages: Record<'zh-CN' | 'zh-TW' | 'en', UpdateMessages> = {
  'zh-CN': {
    errors: {
      busy: '另一项更新操作正在进行。', network: '无法连接更新服务。请检查网络后重试。', 'invalid-release': '发布信息未通过验证。', 'no-assets': '此发布没有可用的桌面更新包。',
      download: '更新文件下载失败。', hash: '更新文件完整性校验失败，已停止安装。', archive: '无法解包更新文件。', bundle: '更新包内容未通过验证。', unsupported: '当前环境不支持自动更新。', permissions: '没有写入应用所需的权限。', apply: '更新替换未完成。', health: '更新后的启动检查失败。', rollback: '恢复旧版本未完成，请关闭应用后重新启动。', ipc: '无法与桌面更新服务通信。',
    },
    updates: '应用更新', desktopOnly: '更新检查仅在 Windows 桌面应用中可用。', check: '检查更新', refresh: '重试读取状态', install: '下载并安装', close: '关闭', cancel: '取消',
    current: '当前版本', candidate: '可用版本', notes: '发布说明', noNotes: '此版本没有提供发布说明。', size: '下载大小', published: '发布时间',
    confirmTitle: '确认更新', confirmBody: '确认后将下载并校验更新文件，然后关闭当前应用、替换程序并重新启动。请先结束未完成的操作。', confirmInstall: '确认下载并重启', checkFailed: '无法读取更新状态。请稍后重试。',
    idle: '尚未检查更新。', checking: '正在检查更新…', available: '发现可用更新。', noUpdate: '此次检查没有发现更新版本。', downloading: '正在下载更新…', verifying: '正在校验更新文件…', staged: '更新文件已就绪，正在准备重启…', applying: '正在应用更新，应用即将关闭…', error: '更新未完成。可以重新检查后重试。', unknownVersion: '暂不可用',
  },
  'zh-TW': {
    errors: {
      busy: '另一項更新操作正在進行。', network: '無法連接更新服務。請檢查網路後重試。', 'invalid-release': '版本資訊未通過驗證。', 'no-assets': '此版本沒有可用的桌面更新套件。',
      download: '更新檔案下載失敗。', hash: '更新檔案完整性驗證失敗，已停止安裝。', archive: '無法解壓縮更新檔案。', bundle: '更新套件內容未通過驗證。', unsupported: '目前環境不支援自動更新。', permissions: '沒有寫入應用程式所需的權限。', apply: '更新替換未完成。', health: '更新後的啟動檢查失敗。', rollback: '舊版本恢復未完成，請關閉應用程式後重新啟動。', ipc: '無法與桌面更新服務通訊。',
    },
    updates: '應用程式更新', desktopOnly: '更新檢查僅適用於 Windows 桌面應用程式。', check: '檢查更新', refresh: '重試讀取狀態', install: '下載並安裝', close: '關閉', cancel: '取消',
    current: '目前版本', candidate: '可用版本', notes: '版本說明', noNotes: '此版本未提供版本說明。', size: '下載大小', published: '發佈時間',
    confirmTitle: '確認更新', confirmBody: '確認後將下載並驗證更新檔案，接著關閉目前應用程式、替換程式並重新啟動。請先完成尚未結束的操作。', confirmInstall: '確認下載並重新啟動', checkFailed: '無法讀取更新狀態。請稍後重試。',
    idle: '尚未檢查更新。', checking: '正在檢查更新…', available: '發現可用更新。', noUpdate: '本次檢查未發現更新版本。', downloading: '正在下載更新…', verifying: '正在驗證更新檔案…', staged: '更新檔案已就緒，正在準備重新啟動…', applying: '正在套用更新，應用程式即將關閉…', error: '更新未完成。請重新檢查後再試。', unknownVersion: '暫時無法取得',
  },
  en: {
    errors: {
      busy: 'Another update operation is in progress.', network: 'Unable to reach the update service. Check your connection and retry.', 'invalid-release': 'Release metadata could not be verified.', 'no-assets': 'This release has no compatible desktop update package.',
      download: 'The update download failed.', hash: 'File integrity verification failed. Installation was stopped.', archive: 'The update could not be extracted.', bundle: 'The update package could not be validated.', unsupported: 'Automatic updates are not supported in this environment.', permissions: 'The app does not have the required write permissions.', apply: 'The update replacement did not complete.', health: 'The updated app failed its startup check.', rollback: 'Restoring the previous version did not complete. Close and restart the app.', ipc: 'Unable to communicate with the desktop update service.',
    },
    updates: 'App updates', desktopOnly: 'Update checks are available only in the Windows desktop app.', check: 'Check for updates', refresh: 'Retry reading status', install: 'Download and install', close: 'Close', cancel: 'Cancel',
    current: 'Current version', candidate: 'Available version', notes: 'Release notes', noNotes: 'No release notes were provided for this version.', size: 'Download size', published: 'Published',
    confirmTitle: 'Confirm update', confirmBody: 'Confirming will download and verify the update, then close the app, replace the executable, and restart. Finish any pending work first.', confirmInstall: 'Confirm download and restart', checkFailed: 'Unable to read update status. Try again later.',
    idle: 'Updates have not been checked.', checking: 'Checking for updates…', available: 'An update is available.', noUpdate: 'This check found no newer version.', downloading: 'Downloading update…', verifying: 'Verifying update files…', staged: 'Update files are ready. Preparing to restart…', applying: 'Applying update. The app will close shortly…', error: 'The update did not complete. Check again before retrying.', unknownVersion: 'Unavailable',
  },
}
