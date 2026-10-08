const rawFS = require('./raw-fs.cjs');
const fs = rawFS.promises;
const path = require('node:path');
const { contained, validateTree, validateBundle } = require('./archive.cjs');
const { REPOSITORY, fail } = require('./policy.cjs');

async function atomicJSON(file, value) {
  const temporary = `${file}.tmp`;
  const handle = await fs.open(temporary, 'w');
  try { await handle.writeFile(JSON.stringify(value)); await handle.sync(); } finally { await handle.close(); }
  await fs.rename(temporary, file);
}
function assertLayout(job, updatesRoot, appData) {
  if (!job || job.schema !== 1 || job.repository !== REPOSITORY || !/^[a-f0-9-]{36}$/.test(job.id) || !Number.isSafeInteger(job.parentPID) || job.parentPID <= 0) fail('apply');
  const jobRoot = path.join(updatesRoot, 'jobs', job.id);
  if (job.jobRoot !== jobRoot || job.helper !== path.join(jobRoot, 'helper') || job.health !== path.join(jobRoot, 'health.json') || !/^[a-f0-9]{64}$/.test(job.nonce)) fail('apply');
  if (path.basename(job.target) !== 'win-x64' || path.basename(path.dirname(job.target)) !== 'desktop-runtime' || contained(appData, job.target) || path.resolve(job.target) === path.resolve(appData)) fail('apply');
  if (job.next !== path.join(path.dirname(job.target), `.x2stock-next-${job.id}`) || job.backup !== path.join(path.dirname(job.target), `.x2stock-backup-${job.id}`)) fail('apply');
  if (!contained(jobRoot, job.helper) || contained(job.target, updatesRoot) || contained(updatesRoot, job.target)) fail('apply');
  if (!job.hashes || !job.previousHashes || !/^[a-f0-9]{40}$/.test(job.sourceSha) || !/^[a-f0-9]{64}$/.test(job.sourceTreeHash ?? '') || typeof job.version !== 'string') fail('apply');
}
async function assertPlainDirectory(directory) {
  const stat = await fs.lstat(directory);
  const native = rawFS.realpathSync.native(directory);
  if (!stat.isDirectory() || stat.isSymbolicLink() || path.resolve(native).toLowerCase() !== path.resolve(directory).toLowerCase()) fail('apply');
}
async function assertAbsent(file) {
  try { await fs.lstat(file); } catch (error) { if (error.code === 'ENOENT') return; throw error; }
  fail('apply');
}
async function renameWithRetry(from, to) {
  // Chromium descendants/AV may release handles shortly after the parent exits.
  // Each directory rename remains atomic; retries are bounded and never copy/delete.
  for (let attempt = 0; ; attempt++) {
    try { return await fs.rename(from, to); } catch (error) {
      if (!['EPERM', 'EACCES', 'EBUSY'].includes(error.code) || attempt >= 39) throw error;
      await require('node:timers/promises').setTimeout(250);
    }
  }
}
async function performSwap(job, { journal, launch, waitHealthy, stop, rename = renameWithRetry }) {
  await assertPlainDirectory(job.target);
  await assertPlainDirectory(job.next);
  await assertAbsent(job.backup);
  await validateTree(job.target, job.previousHashes);
  await validateTree(job.next, job.hashes);
  await validateBundle(job.next, { version: job.version, sourceTreeHash: job.sourceTreeHash });
  let backedUp = false; let replaced = false; let child;
  try {
    await journal('backing-up');
    await rename(job.target, job.backup); backedUp = true;
    await journal('backed-up');
    await rename(job.next, job.target); replaced = true;
    await journal('awaiting-health');
    child = await launch(job.target, true);
    if (!await waitHealthy(child)) fail('health');
    await journal('healthy');
    return 'healthy';
  } catch (error) {
    if (process.env.X2STOCK_TEST_REALM) await atomicJSON(path.join(job.jobRoot, 'swap-error.json'), { code: error.code ?? error.name, stage: { backedUp, replaced, child: Boolean(child) } });
    if (child) await stop(child);
    try {
      if (replaced) await rename(job.target, job.next);
      if (backedUp) await rename(job.backup, job.target);
      await validateTree(job.target, job.previousHashes);
      await journal('rolled-back', error.code === 'health' ? 'health' : 'apply');
      await launch(job.target, false);
      return 'rolled-back';
    } catch { await journal('rollback-failed', 'rollback'); fail('rollback'); }
  }
}
// After a power/process interruption recover only the known immutable transaction paths.
async function recoverSwap(job, journal, launch) {
  const exists = async (file) => { try { await fs.lstat(file); return true; } catch { return false; } };
  if (!await exists(job.backup)) return false;
  await assertPlainDirectory(job.backup);
  await validateTree(job.backup, job.previousHashes);
  if (await exists(job.target)) {
    await assertPlainDirectory(job.target);
    await validateTree(job.target, job.hashes);
    await assertAbsent(job.next);
    await renameWithRetry(job.target, job.next);
  }
  await renameWithRetry(job.backup, job.target);
  await journal('rolled-back', 'apply');
  await launch(job.target, false);
  return true;
}
module.exports = { atomicJSON, assertLayout, assertPlainDirectory, assertAbsent, performSwap, recoverSwap };
