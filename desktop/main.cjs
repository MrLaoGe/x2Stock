const { app, BrowserWindow, Menu, session } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { existsSync } = require('node:fs');

const isDev = process.env.X2STOCK_DEV_SERVER_URL;
// Preserve the Chromium storage origin/profile used by existing previews.
// Reuse the entire legacy root; never copy a live LevelDB or remove old data.
const legacyDataRoot = path.join(app.getPath('appData'), 'XXStock');
const hasLegacyProfile = ['profile', 'session'].some((directory) =>
  existsSync(path.join(legacyDataRoot, directory)));
const appDataRoot = hasLegacyProfile
  ? legacyDataRoot
  : path.join(app.getPath('appData'), 'x2Stock');
app.setPath('userData', path.join(appDataRoot, 'profile'));
app.setPath('cache', path.join(appDataRoot, 'cache'));
app.setPath('sessionData', path.join(appDataRoot, 'session'));
app.setPath('downloads', path.join(appDataRoot, 'downloads'));

function isAllowedNavigation(url) {
  if (isDev) {
    const candidate = new URL(url);
    const developmentOrigin = new URL(isDev);
    return candidate.origin === developmentOrigin.origin;
  }
  return url === pathToFileURL(path.join(__dirname, 'renderer', 'index.html')).href;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 720,
    minHeight: 520,
    show: false,
    backgroundColor: '#1c1c1e',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
    },
  });

  win.once('ready-to-show', () => win.show());
  win.webContents.on('page-title-updated', (event, title) => {
    event.preventDefault();
    win.setTitle(title || 'x2Stock');
  });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => {
    if (!isAllowedNavigation(url)) event.preventDefault();
  });

  const target = isDev
    ? isDev
    : pathToFileURL(path.join(__dirname, 'renderer', 'index.html')).href;
  win.loadURL(target);
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  // Keep renderer permissions closed by default. Future capabilities must be explicit.
  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
