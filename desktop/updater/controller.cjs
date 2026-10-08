const fs = require('./raw-fs.cjs').promises;
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { selectRelease, validateMetadata, validInstall, publicCandidate, fail } = require('./policy.cjs');
const network = require('./network.cjs');
const { extract, validateBundle, treeHashes, hashFile, validateTree, contained } = require('./archive.cjs');
const { atomicJSON, assertLayout, assertPlainDirectory, assertAbsent } = require('./apply.cjs');

function validSender(event, window, rendererURL) {
  if (!window || window.isDestroyed() || event.sender !== window.webContents || event.senderFrame !== window.webContents.mainFrame) return false;
  try { const url = new URL(event.senderFrame.url); url.hash = ''; return url.href === rendererURL; } catch { return false; }
}
class UpdateController {
  constructor({ app, metadata, updatesRoot, appData, target, packaged }) {
    Object.assign(this, { app, metadata, updatesRoot, appData, target, packaged });
    this.status = { revision: 0, phase: 'idle', currentVersion: metadata.version, busy: false };
    this.candidate = null;
    this.offlineCount = 0;
    this.onStatus = () => {};
  }
  getStatus() { return structuredClone(this.status); }
  set(phase, extra = {}) {
    this.status = { revision: this.status.revision + 1, phase, currentVersion: this.metadata.version, busy: ['checking', 'downloading', 'verifying', 'staged', 'applying'].includes(phase), ...(publicCandidate(this.candidate) ? { candidate: publicCandidate(this.candidate) } : {}), ...extra };
    this.onStatus(this.getStatus());
    return this.getStatus();
  }
  error(error) {
    const allowed = ['busy', 'network', 'invalid-release', 'no-assets', 'download', 'hash', 'archive', 'bundle', 'unsupported', 'permissions', 'apply', 'health', 'rollback', 'ipc'];
    return this.set('error', { errorCode: allowed.includes(error.code) ? error.code : 'apply' });
  }
  async restoreResult() {
    try { const value = JSON.parse(await fs.readFile(path.join(this.updatesRoot, 'last-result.json'), 'utf8')); if (value.errorCode) this.error({ code: value.errorCode }); } catch {}
    const lockFile = path.join(this.updatesRoot, 'update.lock');
    try {
      const lock = JSON.parse(await fs.readFile(lockFile, 'utf8'));
      const alive = (pid) => { if (!Number.isSafeInteger(pid) || pid <= 0) return false; try { process.kill(pid, 0); return true; } catch (error) { return error.code !== 'ESRCH'; } };
      if (!alive(lock.parentPID) && !alive(lock.helperPID)) {
        await fs.unlink(lockFile);
        this.error({ code: 'apply' });
      }
    } catch {}
  }
  async check() {
    if (this.status.busy) return this.getStatus();
    this.set('checking');
    try {
      this.candidate = selectRelease(await network.releases(), this.metadata.version);
      if (!this.candidate) { this.offlineCount = 0; return this.set('no-update', { errorCode: 'no-assets' }); }
      const commit = await network.tagCommit(this.candidate.tag);
      const result = await network.request(this.candidate.archive.browser_download_url, { kind: 'asset', limit: 16384, expectedSize: this.candidate.archive.size });
      if (result.digest !== this.candidate.digest) fail('hash');
      let metadata; try { metadata = JSON.parse(result.body.toString('utf8')); } catch { fail('invalid-release'); }
      this.candidate.metadata = validateMetadata(metadata, this.candidate, commit);
      this.candidate.sourceSha = commit;
      this.candidate.sizeBytes = this.candidate.metadata.archive_size;
      this.offlineCount = 0;
      return this.set('available');
    } catch (error) { this.candidate = null; this.offlineCount++; return this.error(error); }
  }
  startBackground() {
    const run = async () => {
      if (!this.status.busy) await this.check();
      this.timer = setTimeout(run, Math.min(24, 6 * 2 ** Math.min(this.offlineCount, 2)) * 60 * 60 * 1000);
      this.timer.unref();
    };
    this.timer = setTimeout(run, 2000); this.timer.unref();
  }
  stopBackground() { clearTimeout(this.timer); }
  async install(payload) {
    if (this.status.busy) return this.getStatus();
    if (!validInstall(payload, this.candidate) || this.status.phase !== 'available') return this.error({ code: 'ipc' });
    if (!this.packaged || process.platform !== 'win32' || process.arch !== 'x64') return this.error({ code: 'unsupported' });
    let lock; let next; let ownsLock = false;
    try {
      if (path.basename(this.target) !== 'win-x64' || path.basename(path.dirname(this.target)) !== 'desktop-runtime' || contained(this.appData, this.target)) fail('unsupported');
      await fs.mkdir(this.updatesRoot, { recursive: true });
      await assertPlainDirectory(this.updatesRoot);
      await assertPlainDirectory(path.dirname(this.updatesRoot));
      await assertPlainDirectory(path.dirname(path.dirname(this.updatesRoot)));
      try { lock = await fs.open(path.join(this.updatesRoot, 'update.lock'), 'wx'); } catch { fail('busy'); }
      ownsLock = true;
      await lock.writeFile(JSON.stringify({ parentPID: process.pid })); await lock.sync();
      const id = crypto.randomUUID();
      const jobRoot = path.join(this.updatesRoot, 'jobs', id);
      const archive = path.join(jobRoot, 'source.zip');
      const unpacked = path.join(jobRoot, 'runtime');
      const helper = path.join(jobRoot, 'helper');
      next = path.join(path.dirname(this.target), `.x2stock-next-${id}`);
      const backup = path.join(path.dirname(this.target), `.x2stock-backup-${id}`);
      await fs.mkdir(jobRoot, { recursive: true });
      await assertPlainDirectory(jobRoot);
      await assertPlainDirectory(this.target);
      await assertPlainDirectory(path.dirname(this.target));
      await assertAbsent(next); await assertAbsent(backup);
      const currentHash = await treeHashes(this.target);
      await validateBundle(this.target, { version: this.metadata.version, sourceTreeHash: this.metadata.source_tree_hash });
      this.set('downloading', { downloadedBytes: 0 });
      const candidate = this.candidate;
      const download = await network.request(candidate.metadata.archive_url, { kind: 'archive', timeout: 5 * 60 * 1000, file: archive, limit: candidate.metadata.archive_size, expectedSize: candidate.metadata.archive_size, progress: (downloadedBytes) => this.set('downloading', { downloadedBytes }) });
      this.set('verifying');
      if (download.digest !== candidate.metadata.archive_sha256) fail('hash');
      await extract(archive, unpacked, { runtimeOnly: true, sourceTreeHash: candidate.metadata.source_tree_hash, sourceSha: candidate.sourceSha });
      await validateBundle(unpacked, { version: candidate.version, sourceTreeHash: candidate.metadata.source_tree_hash });
      const hashes = await treeHashes(unpacked);
      await fs.cp(unpacked, next, { recursive: true, errorOnExist: true, force: false });
      await validateTree(next, hashes);
      await fs.cp(this.target, helper, { recursive: true, errorOnExist: true, force: false });
      await validateTree(helper, currentHash);
      const job = { schema: 1, repository: 'MrLaoGe/x2Stock', id, jobRoot, helper, health: path.join(jobRoot, 'health.json'), nonce: crypto.randomBytes(32).toString('hex'), parentPID: process.pid, target: this.target, next, backup, version: candidate.version, sourceSha: candidate.sourceSha, sourceTreeHash: candidate.metadata.source_tree_hash, hashes, previousHashes: currentHash };
      assertLayout(job, this.updatesRoot, this.appData);
      const file = path.join(jobRoot, 'job.json');
      await fs.writeFile(file, JSON.stringify(job), { flag: 'wx' });
      const digest = await hashFile(file);
      await fs.writeFile(path.join(jobRoot, 'job.sha256'), digest, { flag: 'wx' });
      await require('./recovery.cjs').prepareRecovery(job, digest);
      await atomicJSON(path.join(jobRoot, 'journal.json'), { id, phase: 'staged', target: job.target, version: job.version, sourceSha: job.sourceSha });
      this.set('staged');
      await lock.close(); lock = null;
      const child = spawn(path.join(helper, 'x2Stock.exe'), [`--x2stock-update-helper=${id}`, `--x2stock-update-digest=${digest}`], { detached: true, windowsHide: true, stdio: 'ignore', cwd: helper });
      await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
      child.once('error', () => {}); child.unref();
      await atomicJSON(path.join(this.updatesRoot, 'update.lock'), { parentPID: process.pid, helperPID: child.pid, id });
      const status = this.set('applying');
      setTimeout(() => this.app.quit(), 1000);
      return status;
    } catch (error) {
      // Existing runtime/data untouched on every download/staging failure.
      if (lock) await lock.close();
      if (ownsLock) await fs.unlink(path.join(this.updatesRoot, 'update.lock')).catch(() => {});
      return this.error(error);
    }
  }
}
function registerIPC({ ipcMain, controller, getWindow, rendererURL }) {
  for (const [channel, operation] of [['x2stock:update:status', 'getStatus'], ['x2stock:update:check', 'check'], ['x2stock:update:install', 'install']]) {
    ipcMain.handle(channel, (event, ...args) => {
      if (!validSender(event, getWindow(), rendererURL) || args.length !== (operation === 'install' ? 1 : 0)) return { ...controller.getStatus(), phase: 'error', errorCode: 'ipc' };
      return controller[operation](...args);
    });
  }
}
module.exports = { UpdateController, validSender, registerIPC };
