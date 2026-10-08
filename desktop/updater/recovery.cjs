// Fixed local bootstrap survives the gap between the two runtime renames.
const rawFS = require('./raw-fs.cjs');
const fs = rawFS.promises;
const path = require('node:path');
const { treeHashes, validateTree } = require('./archive.cjs');
const { assertPlainDirectory, atomicJSON } = require('./apply.cjs');
const { fail } = require('./policy.cjs');
const recoveryRoot = (target) => path.join(path.dirname(target), '.recovery');
const pendingFile = (target) => path.join(recoveryRoot(target), 'pending.json');
async function prepareRecovery(job, digest) {
  const root = recoveryRoot(job.target);
  await assertPlainDirectory(path.dirname(job.target));
  try {
    await fs.lstat(root);
    try { await fs.lstat(path.join(root, 'pending.json')); fail('busy'); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    await assertPlainDirectory(root);
    await fs.rename(root, path.join(path.dirname(root), `.x2stock-recovery-${job.id}`));
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  await fs.cp(job.target, root, { recursive: true, errorOnExist: true, force: false });
  await validateTree(root, job.previousHashes);
  await atomicJSON(path.join(root, 'pending.json'), { schema: 1, id: job.id, digest });
}
async function clearPending(job) {
  await fs.unlink(pendingFile(job.target)).catch((error) => { if (error.code !== 'ENOENT') throw error; });
}
async function readPending(target) {
  const root = recoveryRoot(target);
  await assertPlainDirectory(root);
  const file = pendingFile(target); const stat = await fs.lstat(file);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 1024) fail('apply');
  const marker = JSON.parse(await fs.readFile(file, 'utf8'));
  if (Object.keys(marker).sort().join(',') !== 'digest,id,schema' || marker.schema !== 1 || !/^[a-f0-9-]{36}$/.test(marker.id) || !/^[a-f0-9]{64}$/.test(marker.digest)) fail('apply');
  return marker;
}
async function runRecovery({ executable, appData, updatesRoot }) {
  const ownRoot = path.dirname(rawFS.realpathSync.native(executable));
  const target = path.join(path.dirname(ownRoot), 'win-x64');
  if (!['win-x64', '.recovery'].includes(path.basename(ownRoot)) || path.basename(path.dirname(ownRoot)) !== 'desktop-runtime') fail('apply');
  await assertPlainDirectory(path.dirname(ownRoot));
  const marker = await readPending(target);
  const { readJob, runHelper } = require('./helper.cjs');
  const file = path.join(updatesRoot, 'jobs', marker.id, 'job.json');
  const job = await readJob(file, marker.digest, updatesRoot, appData);
  if (path.resolve(job.target).toLowerCase() !== path.resolve(target).toLowerCase()) fail('apply');
  const copy = await treeHashes(recoveryRoot(target)); delete copy['pending.json'];
  if (JSON.stringify(Object.entries(copy).sort()) !== JSON.stringify(Object.entries(job.previousHashes).sort())) fail('hash');
  // Another live helper owns the transaction; never race its renames.
  try {
    const lock = JSON.parse(await fs.readFile(path.join(updatesRoot, 'update.lock'), 'utf8'));
    if (lock.helperPID !== process.pid && Number.isSafeInteger(lock.helperPID) && lock.helperPID > 0) {
      try { process.kill(lock.helperPID, 0); fail('busy'); } catch (error) { if (error.code !== 'ESRCH') throw error; }
    }
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (path.basename(ownRoot) === 'win-x64') {
    // Windows cannot rename a directory containing this process's running EXE.
    // The normal startup only dispatches the verified fixed bootstrap and exits.
    const child = require('node:child_process').spawn(path.join(recoveryRoot(target), 'x2Stock.exe'), ['--x2stock-recover'], { detached: true, windowsHide: true, stdio: 'ignore', cwd: recoveryRoot(target) });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.once('error', () => {}); child.unref();
    return;
  }
  await runHelper({ file, digest: marker.digest, updatesRoot, appData, recovery: true });
}
module.exports = { recoveryRoot, pendingFile, prepareRecovery, clearPending, readPending, runRecovery };
