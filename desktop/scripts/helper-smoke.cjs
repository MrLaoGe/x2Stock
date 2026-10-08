// Local Windows fixture only; never contacts a release or modifies shipped artifacts.
// Usage: node desktop/scripts/helper-smoke.cjs <fresh-empty-fixture-root> healthy|blank
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const os = require('node:os');
const { spawn } = require('node:child_process');
const { setTimeout: delay } = require('node:timers/promises');
const { execFileSync } = require('node:child_process');
const { treeHashes, hashFile, validateTree } = require('../updater/archive.cjs');
const { atomicJSON, assertLayout } = require('../updater/apply.cjs');
let cleanupRoot;
async function cleanupOwned() {
  if (!cleanupRoot) return;
  const prefix = `${cleanupRoot}${path.sep}`.replace(/'/g, "''");
  const script = `$ErrorActionPreference='Stop';$items=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'x2Stock.exe' -and $_.ExecutablePath -and $_.ExecutablePath.StartsWith('${prefix}',[StringComparison]::OrdinalIgnoreCase) });foreach($item in $items){$p=Get-Process -Id $item.ProcessId -ErrorAction SilentlyContinue;if($p -and $p.MainWindowHandle -ne 0){[void]$p.CloseMainWindow();[void]$p.WaitForExit(5000)}};$remaining=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'x2Stock.exe' -and $_.ExecutablePath -and $_.ExecutablePath.StartsWith('${prefix}',[StringComparison]::OrdinalIgnoreCase) });foreach($item in $remaining){Stop-Process -Id $item.ProcessId -Force -ErrorAction SilentlyContinue}`;
  execFileSync('powershell.exe', ['-NoProfile', '-Command', script], { stdio: 'ignore', windowsHide: true });
}

async function cdp(port, method, params = {}) {
  const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(pages[0].webSocketDebuggerUrl);
    const timer = setTimeout(() => { socket.close(); reject(new Error('CDP timeout')); }, 5000);
    socket.onopen = () => socket.send(JSON.stringify({ id: 1, method, params }));
    socket.onmessage = ({ data }) => { const value = JSON.parse(data); if (value.id === 1) { clearTimeout(timer); socket.close(); value.error ? reject(new Error('CDP rejected')) : resolve(value.result); } };
    socket.onerror = () => { clearTimeout(timer); reject(new Error('CDP failed')); };
  });
}
async function run() {
  let root = path.resolve(process.argv[2] ?? ''); const mode = process.argv[3];
  if (!['healthy', 'blank', 'interrupt-backup', 'interrupt-target'].includes(mode) || !process.argv[2]) throw new Error('Supply fresh fixture root and healthy|blank|interrupt-backup|interrupt-target');
  try { await fs.lstat(root); throw new Error('Fixture root already exists: refuse overwrite'); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const temp = require('node:fs').realpathSync.native(os.tmpdir());
  root = path.join(temp, path.basename(root));
  if (!path.basename(root).startsWith('x2stock-fixture-') || !require('../updater/archive.cjs').contained(temp, root)) throw new Error('Fixture must be x2stock-fixture-* beneath OS temp');
  await fs.mkdir(root); root = require('node:fs').realpathSync.native(root);
  cleanupRoot = root;
  const nonce = crypto.randomBytes(32).toString('hex');
  await fs.writeFile(path.join(root, '.x2stock-test-fixture.json'), JSON.stringify({ schema: 1, root, nonce }), { flag: 'wx' });
  const env = { ...process.env, X2STOCK_TEST_REALM: root, X2STOCK_TEST_NONCE: nonce, X2STOCK_TEST_OFFLINE: '1' };
  const appData = path.join(root, 'state', 'appdata');
  const source = path.resolve(__dirname, '..', 'release', 'win-unpacked');
  const target = path.join(root, 'project', 'desktop-runtime', 'win-x64');
  const id = crypto.randomUUID();
  const updatesRoot = path.join(appData, 'x2Stock', 'updates');
  const jobRoot = path.join(updatesRoot, 'jobs', id);
  const next = path.join(path.dirname(target), `.x2stock-next-${id}`);
  const backup = path.join(path.dirname(target), `.x2stock-backup-${id}`);
  const helper = path.join(jobRoot, 'helper');
  await fs.mkdir(jobRoot, { recursive: true });
  await fs.cp(source, target, { recursive: true, force: false, errorOnExist: true });
  await fs.cp(source, next, { recursive: true, force: false, errorOnExist: true });
  await fs.cp(source, helper, { recursive: true, force: false, errorOnExist: true });
  const beforeData = path.join(root, 'project', '.env'); await fs.writeFile(beforeData, 'synthetic retained data');
  const metadata = JSON.parse(await fs.readFile(path.join(next, 'resources', 'build-manifest.json'), 'utf8'));
  const previousHashes = await treeHashes(target); const hashes = await treeHashes(next);
  const parent = spawn(path.join(target, 'x2Stock.exe'), ['--remote-debugging-port=9241', '--host-resolver-rules=MAP * ~NOTFOUND'], { env, cwd: path.dirname(target), stdio: ['ignore', 'pipe', 'pipe'] });
  parent.stdout.on('data', (data) => process.stdout.write(data));
  parent.stderr.on('data', (data) => process.stderr.write(data));
  await new Promise((resolve, reject) => { parent.once('spawn', resolve); parent.once('error', reject); });
  await delay(5000);
  if (parent.exitCode !== null) throw new Error('Fixture exited before health: close any existing x2Stock instance');
  const pages = await (await fetch('http://127.0.0.1:9241/json/list')).json();
  if (!pages[0].url.startsWith(require('node:url').pathToFileURL(path.join(target, 'resources', 'app.asar', 'renderer', 'index.html')).href)) throw new Error('CDP belongs to another application: refuse to operate');
  const rendered = await cdp(9241, 'Runtime.evaluate', { expression: 'document.querySelector("#root").innerText.length', returnByValue: true });
  if (!(rendered.result.value > 0)) throw new Error('Old fixture renderer empty');
  await cdp(9241, 'Runtime.evaluate', { expression: 'localStorage.setItem("x2stock.language","en"); true', returnByValue: true });
  const job = { schema: 1, repository: 'MrLaoGe/x2Stock', id, jobRoot, helper, health: path.join(jobRoot, 'health.json'), nonce: crypto.randomBytes(32).toString('hex'), parentPID: parent.pid, target, next, backup, version: metadata.version, sourceSha: metadata.build_source_sha, sourceTreeHash: metadata.source_tree_hash, hashes, previousHashes };
  assertLayout(job, updatesRoot, appData);
  const file = path.join(jobRoot, 'job.json'); await fs.writeFile(file, JSON.stringify(job), { flag: 'wx' });
  const digest = await hashFile(file); await fs.writeFile(path.join(jobRoot, 'job.sha256'), digest, { flag: 'wx' });
  await require('../updater/recovery.cjs').prepareRecovery(job, digest);
  await atomicJSON(path.join(jobRoot, 'journal.json'), { id, phase: 'staged', target });
  const helperEnv = { ...env, ...(mode === 'blank' ? { X2STOCK_TEST_EMPTY_RENDERER: '1' } : {}), ...(mode.startsWith('interrupt-') ? { X2STOCK_TEST_PAUSE_PHASE: mode === 'interrupt-backup' ? 'backed-up' : 'awaiting-health' } : {}) };
  const child = spawn(path.join(helper, 'x2Stock.exe'), [`--x2stock-update-helper=${id}`, `--x2stock-update-digest=${digest}`], { env: helperEnv, cwd: helper, windowsHide: true, stdio: 'ignore' });
  await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
  await cdp(9241, 'Runtime.evaluate', { expression: 'setTimeout(()=>window.close(),100); true', returnByValue: true });
  if (mode.startsWith('interrupt-')) {
    let paused;
    for (let i = 0; i < 150; i++) { try { paused = JSON.parse(await fs.readFile(path.join(jobRoot, 'paused.json'), 'utf8')); } catch {} if (paused) break; await delay(200); }
    if (!paused || paused.pid !== child.pid) throw new Error('Helper never reached owned kill point');
    execFileSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    await delay(1000);
    const bat = '@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\nif exist "desktop-runtime\\win-x64\\x2Stock.exe" (\r\n start "" "desktop-runtime\\win-x64\\x2Stock.exe"\r\n) else (\r\n start "" "desktop-runtime\\.recovery\\x2Stock.exe" --x2stock-recover\r\n)\r\n';
    await fs.writeFile(path.join(root, 'project', '启动.bat'), bat);
    const boot = spawn('cmd.exe', ['/d', '/c', '启动.bat'], { env, cwd: path.join(root, 'project'), windowsHide: true, stdio: 'ignore' });
    await new Promise((resolve, reject) => { boot.once('exit', resolve); boot.once('error', reject); });
  }
  let journal;
  for (let i = 0; i < 225; i++) {
    try { journal = JSON.parse(await fs.readFile(path.join(jobRoot, 'journal.json'), 'utf8')); } catch {}
    if (['healthy', 'rolled-back', 'rollback-failed'].includes(journal?.phase)) break;
    await delay(200);
  }
  await validateTree(target, mode === 'healthy' ? hashes : previousHashes);
  if (journal?.phase !== (mode === 'healthy' ? 'healthy' : 'rolled-back')) throw new Error(`Unexpected helper result: ${JSON.stringify(journal)}`);
  if (await fs.readFile(beforeData, 'utf8') !== 'synthetic retained data') throw new Error('Project data changed');
  for (let i = 0; i < 100 && child.exitCode === null; i++) await delay(200);
  if (child.exitCode === null && !mode.startsWith('interrupt-')) throw new Error('Helper did not exit after final journal');
  await delay(5000);
  let finalPage;
  for (let i = 0; i < 100; i++) {
    try {
      const value = await cdp(9242, 'Runtime.evaluate', { expression: '({url:location.href,rootLength:document.querySelector("#root")?.innerText.trim().length||0,language:localStorage.getItem("x2stock.language"),lang:document.documentElement.lang,title:document.title})', returnByValue: true });
      finalPage = value.result.value;
      if (finalPage.url.startsWith(require('node:url').pathToFileURL(path.join(target, 'resources', 'app.asar', 'renderer', 'index.html')).href) && finalPage.rootLength > 0 && finalPage.language === 'en' && finalPage.lang === 'en') break;
    } catch {} await delay(200);
  }
  if (!finalPage?.rootLength || finalPage.language !== 'en' || finalPage.lang !== 'en') throw new Error(`Reopened runtime/profile did not render the expected retained language: ${JSON.stringify(finalPage)}`);
  const owned = JSON.parse(execFileSync('powershell.exe', ['-NoProfile', '-Command', `@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'x2Stock.exe' -and $_.ExecutablePath -eq '${path.join(target, 'x2Stock.exe').replace(/'/g, "''")}' } | ForEach-Object {$p=Get-Process -Id $_.ProcessId;[pscustomobject]@{pid=$p.Id;title=$p.MainWindowTitle;handle=$p.MainWindowHandle.ToInt64();responding=$p.Responding}}) | ConvertTo-Json -Compress`], { encoding: 'utf8', windowsHide: true }));
  if (!owned.some((p) => p.handle > 0 && p.responding && p.title === finalPage.title)) throw new Error('Owned native window not visible/responding');
  console.log(JSON.stringify({ root, mode, helperPID: child.pid, helperExitCode: child.exitCode, survivedHelperExitMs: 5000, parentPID: parent.pid, oldRootLength: rendered.result.value, finalPage, owned, journal, retainedData: true, expectedSameVersionFixture: true }));
  child.unref(); parent.unref();
}
run().catch((error) => { console.error(error.message); process.exitCode = 1; }).finally(cleanupOwned);
