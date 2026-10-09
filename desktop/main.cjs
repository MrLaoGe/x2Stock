const { app, BrowserWindow, Menu, session, ipcMain, nativeTheme } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { existsSync } = require('node:fs');
const fs = require('node:fs');
let fixtureData;
// Test mode cannot affect the installed/user app: it requires a marked temp
// runtime copy and uses a separate profile, instance domain and helper staging.
try {
  fixtureData = require('./updater/fixture.cjs').fixtureAppData();
  if (fixtureData) {
    app.setPath('appData', fixtureData);
    app.commandLine.appendSwitch('enable-automation');
    if (process.env.X2STOCK_TEST_CDP_PORT) {
      const port = Number(process.env.X2STOCK_TEST_CDP_PORT);
      if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid test port');
      app.commandLine.appendSwitch('remote-debugging-port', String(port));
      app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1');
    }
    if (process.env.X2STOCK_TEST_OFFLINE === '1') {
      app.commandLine.appendSwitch('host-resolver-rules', 'MAP * ~NOTFOUND');
      // Chromium DNS switches do not affect Node fetch; block that test path too.
      require('./updater/network.cjs').setFixtureOffline(true);
    }
  }
} catch (error) { console.error('Test realm rejected:', error.code ?? error.message); app.exit(1); }

const helperArg = process.argv?.find((arg) => arg.startsWith('--x2stock-update-helper='));
const healthArg = process.argv?.find((arg) => arg.startsWith('--x2stock-update-health='));
const healthId = healthArg?.split('=')[1] || app.commandLine?.getSwitchValue('x2stock-update-health');
const recoveryMode = !helperArg && !healthId && (process.argv.includes('--x2stock-recover') || require('./updater/raw-fs.cjs').existsSync(require('./updater/recovery.cjs').pendingFile(path.join(path.dirname(path.dirname(process.execPath)), 'win-x64'))));
if (process.env.X2STOCK_TEST_REALM) console.log('Fixture bootstrap', JSON.stringify({ helper: Boolean(helperArg), health: Boolean(healthId) }));
if (recoveryMode) {
  const appData = fixtureData || app.getPath('appData');
  const updatesRoot = path.join(appData, 'x2Stock', 'updates');
  app.setPath('userData', path.join(updatesRoot, 'recovery-profile'));
  app.setPath('sessionData', path.join(updatesRoot, 'recovery-profile'));
  app.whenReady().then(async () => {
    try { await require('./updater/recovery.cjs').runRecovery({ executable: process.execPath, appData, updatesRoot }); app.exit(0); }
    catch (error) { if (fixtureData) console.error('Fixture recovery failed', error.code ?? error.name); app.exit(1); }
  });
} else if (helperArg) {
  const id = helperArg.split('=')[1];
  const digest = process.argv.find((arg) => arg.startsWith('--x2stock-update-digest='))?.split('=')[1];
  if (!/^[a-f0-9-]{36}$/.test(id) || !/^[a-f0-9]{64}$/.test(digest ?? '')) app.exit(1);
  else {
    const appData = fixtureData || app.getPath('appData');
    const updatesRoot = path.join(appData, 'x2Stock', 'updates');
    const jobRoot = path.join(updatesRoot, 'jobs', id);
    // Helper mode is selected before legacy profile and instance-lock setup.
    app.setPath('userData', path.join(jobRoot, 'helper-profile'));
    app.setPath('sessionData', path.join(jobRoot, 'helper-profile'));
    app.whenReady().then(async () => {
      try { await require('./updater/helper.cjs').runHelper({ file: path.join(jobRoot, 'job.json'), digest, updatesRoot, appData }); app.exit(0); }
      catch { app.exit(1); }
    });
  }
} else {

const isDev = process.env.X2STOCK_DEV_SERVER_URL;
// Preserve the Chromium storage origin/profile used by existing previews.
// Reuse the entire legacy root; never copy a live LevelDB or remove old data.
const selectedAppData = fixtureData || app.getPath('appData');
const legacyDataRoot = path.join(selectedAppData, 'XXStock');
const hasLegacyProfile = ['profile', 'session'].some((directory) =>
  existsSync(path.join(legacyDataRoot, directory)));
const appDataRoot = hasLegacyProfile
  ? legacyDataRoot
  : path.join(selectedAppData, 'x2Stock');
app.setPath('userData', path.join(appDataRoot, 'profile'));
app.setPath('cache', path.join(appDataRoot, 'cache'));
app.setPath('sessionData', path.join(appDataRoot, 'session'));
app.setPath('downloads', path.join(appDataRoot, 'downloads'));
if (app.requestSingleInstanceLock && !app.requestSingleInstanceLock()) app.quit();
let mainWindow;
let updater;
let buildMetadata;
const updatesRoot = path.join(selectedAppData, 'x2Stock', 'updates');

function isAllowedNavigation(url) {
  if (isDev) {
    const candidate = new URL(url);
    const developmentOrigin = new URL(isDev);
    return candidate.origin === developmentOrigin.origin;
  }
  return url === pathToFileURL(path.join(__dirname, 'renderer', 'index.html')).href;
}

function createWindow() {
  // Match the dark workspace even when Windows uses a light system theme.
  // Keep native caption buttons, drag, snap and accessibility behavior.
  nativeTheme.themeSource = 'dark';
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
      additionalArguments: [`--x2stock-version=${app.getVersion()}`],
    },
  });
  mainWindow = win;
  win.__rendererPath = path.join(__dirname, 'renderer');

  win.once('ready-to-show', () => win.show());
  win.webContents.on('page-title-updated', (event, title) => {
    event.preventDefault();
    win.setTitle(title || 'x2Stock');
  });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => {
    if (!isAllowedNavigation(url)) event.preventDefault();
  });
  win.webContents.once('did-finish-load', () => {
    if (fixtureData && healthId && process.env.X2STOCK_TEST_EMPTY_RENDERER === '1') {
      win.webContents.executeJavaScript('new MutationObserver(()=>{const r=document.querySelector("#root");if(r?.childNodes.length)r.replaceChildren()}).observe(document.body,{childList:true,subtree:true}); document.querySelector("#root")?.replaceChildren()');
    }
    if (process.env.X2STOCK_TEST_REALM) console.log('Fixture local page finished', JSON.stringify({ health: Boolean(healthId) }));
    if (healthId && process.env.X2STOCK_TEST_REALM) {
      try { require('./updater/raw-fs.cjs').writeFileSync(path.join(updatesRoot, 'jobs', healthId, 'health-start.json'), JSON.stringify({ received: true })); }
      catch (error) { console.log('Fixture health-start failure', JSON.stringify({ code: error.code ?? error.name, healthId, expectedRoot: updatesRoot === path.join(process.env.X2STOCK_TEST_REALM, 'state', 'appdata', 'x2Stock', 'updates') })); }
    }
    if (healthId) require('./updater/helper.cjs').acknowledge({ id: healthId, updatesRoot, appData: selectedAppData, target: path.dirname(process.execPath), metadata: buildMetadata, window: win });
    updater.startBackground();
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
  const metadataPath = app.isPackaged
    ? path.join(process.resourcesPath, 'build-manifest.json')
    : path.join(__dirname, 'build', 'build-manifest.json');
  buildMetadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
  if (buildMetadata.version !== app.getVersion() || buildMetadata.repository !== 'MrLaoGe/x2Stock') throw new Error('Bundled version metadata mismatch');
  const { UpdateController, registerIPC } = require('./updater/controller.cjs');
  updater = new UpdateController({ app, metadata: buildMetadata, updatesRoot, appData: selectedAppData, target: path.dirname(process.execPath), packaged: app.isPackaged });
  updater.onStatus = (status) => { if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('x2stock:update:changed', status); };
  registerIPC({ ipcMain, controller: updater, getWindow: () => mainWindow, rendererURL: pathToFileURL(path.join(__dirname, 'renderer', 'index.html')).href });
  updater.restoreResult();
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});
app.on('second-instance', () => { if (mainWindow) { if (mainWindow.isMinimized()) mainWindow.restore(); mainWindow.focus(); } });
app.on('before-quit', () => updater?.stopBackground());

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
}
