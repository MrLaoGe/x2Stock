const fs = require('./raw-fs.cjs').promises;
const rawFS = require('./raw-fs.cjs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { setTimeout: delay } = require('node:timers/promises');
const { assertLayout, atomicJSON, performSwap, recoverSwap } = require('./apply.cjs');
const { hashFile, validateTree } = require('./archive.cjs');
const { fail } = require('./policy.cjs');
async function terminalRecovery(state, job, { recovery, validate = validateTree, launch, restore, journal }) {
  if (!['healthy', 'rolled-back', 'rollback-failed'].includes(state?.phase)) return false;
  if (!recovery) return true;
  if (state.phase === 'rollback-failed') {
    if (!await restore(job, journal, launch)) fail('rollback');
  } else {
    await validate(job.target, state.phase === 'healthy' ? job.hashes : job.previousHashes);
    await launch(job.target, false);
  }
  return true;
}

async function readJob(file, digest, updatesRoot, appData) {
  const stat = await fs.lstat(file);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 2 * 1024 * 1024 || await hashFile(file) !== digest) fail('apply');
  const job = JSON.parse(await fs.readFile(file, 'utf8'));
  assertLayout(job, updatesRoot, appData);
  if (file !== path.join(job.jobRoot, 'job.json')) fail('apply');
  return job;
}
async function runHelper({ file, digest, updatesRoot, appData, recovery = false }) {
  const job = await readJob(file, digest, updatesRoot, appData);
  const journalFile = path.join(job.jobRoot, 'journal.json');
  const journal = async (phase, errorCode) => {
    await atomicJSON(journalFile, { id: job.id, phase, errorCode, target: job.target, version: job.version, sourceSha: job.sourceSha });
    if (process.env.X2STOCK_TEST_REALM && process.env.X2STOCK_TEST_PAUSE_PHASE === phase && !recovery) {
      await fs.writeFile(path.join(job.jobRoot, 'paused.json'), JSON.stringify({ phase, pid: process.pid }));
      await delay(60000);
    }
    if (phase === 'rolled-back' || phase === 'rollback-failed') await atomicJSON(path.join(updatesRoot, 'last-result.json'), { version: job.version, errorCode });
  };
  const launch = async (target, health) => {
    if (!health) await require('./recovery.cjs').clearPending(job);
    const args = health ? [`--x2stock-update-health=${job.id}`] : [];
    if (process.env.X2STOCK_TEST_REALM) args.push('--remote-debugging-port=9242');
    const logFD = process.env.X2STOCK_TEST_REALM ? rawFS.openSync(path.join(job.jobRoot, 'candidate.log'), 'a') : null;
    let child;
    try { child = spawn(path.join(target, 'x2Stock.exe'), args, { cwd: path.dirname(target), detached: true, windowsHide: false, stdio: logFD === null ? 'ignore' : ['ignore', logFD, logFD] }); }
    finally { if (logFD !== null) rawFS.closeSync(logFD); }
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.once('error', () => {}); child.unref(); return child;
  };
  const stop = async (child) => {
    if (child.exitCode !== null) return;
    // Numeric PID only, no shell and no arbitrary command text.
    const terminator = spawn('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
    await new Promise((resolve) => { terminator.once('exit', resolve); terminator.once('error', resolve); });
    for (let i = 0; i < 20 && child.exitCode === null; i++) await delay(100);
    if (child.exitCode === null) fail('rollback');
  };
  const waitHealthy = async (child) => {
    for (let i = 0; i < 150; i++) {
      if (child.exitCode !== null) return false;
      try {
        const ack = JSON.parse(await fs.readFile(job.health, 'utf8'));
        if (ack.id === job.id && ack.nonce === job.nonce && ack.pid === child.pid && ack.version === job.version && ack.sourceTreeHash === job.sourceTreeHash && ack.rootLength > 0) return true;
      } catch {}
      await delay(200);
    }
    return false;
  };
  try {
    try {
      const state = JSON.parse(await fs.readFile(journalFile, 'utf8'));
      if (await terminalRecovery(state, job, { recovery, launch, restore: recoverSwap, journal })) return;
    } catch (error) { if (error.code && error.code !== 'ENOENT') throw error; }
    await journal('waiting-parent');
    for (let i = 0; i < 300; i++) {
      try { process.kill(job.parentPID, 0); } catch (error) { if (error.code === 'ESRCH') break; }
      if (i === 299) fail('busy');
      await delay(200);
    }
    if (await recoverSwap(job, journal, launch)) return;
    await journal('validating');
    const result = await performSwap(job, { journal, launch, waitHealthy, stop });
    if (result === 'healthy') await require('./recovery.cjs').clearPending(job);
    const state = JSON.parse(await fs.readFile(journalFile, 'utf8'));
    const record = result === 'healthy' ? {} : { version: job.version, errorCode: state.errorCode === 'health' ? 'health' : 'apply' };
    await atomicJSON(path.join(updatesRoot, 'last-result.json'), record);
  } catch (error) {
    await journal('failed', ['rollback', 'health', 'busy'].includes(error.code) ? error.code : 'apply');
    await atomicJSON(path.join(updatesRoot, 'last-result.json'), { version: job.version, errorCode: ['rollback', 'health', 'busy'].includes(error.code) ? error.code : 'apply' });
    // If validation failed before the swap, reopen the verified old app.
    try { await validateTree(job.target, job.previousHashes); await launch(job.target, false); } catch {}
    if (recovery) throw error;
  } finally {
    await fs.unlink(path.join(updatesRoot, 'update.lock')).catch(() => {});
  }
}
async function acknowledge({ id, updatesRoot, appData, target, metadata, window }) {
  if (!/^[a-f0-9-]{36}$/.test(id)) return;
  let stage = 'read-job';
  const observation = path.join(updatesRoot, 'jobs', id, 'health-observation.json');
  try {
    const file = path.join(updatesRoot, 'jobs', id, 'job.json');
    const digestFile = path.join(updatesRoot, 'jobs', id, 'job.sha256');
    const job = await readJob(file, (await fs.readFile(digestFile, 'utf8')).trim(), updatesRoot, appData);
    stage = 'metadata';
    if (path.resolve(job.target).toLowerCase() !== path.resolve(target).toLowerCase() || job.sourceTreeHash !== metadata.source_tree_hash || job.version !== metadata.version) { await atomicJSON(observation, { stage, matches: false }); return; }
    const expectedURL = require('node:url').pathToFileURL(path.join(window.__rendererPath, 'index.html')).href;
    for (let i = 0; i < 100 && !window.isDestroyed(); i++) {
      stage = 'renderer';
      const value = await window.webContents.executeJavaScript('({rootLength:document.querySelector("#root")?.innerText.trim().length || 0, url:location.href})');
      const actual = new URL(value.url); actual.hash = '';
      if (actual.href !== expectedURL) { await atomicJSON(observation, { stage, matches: false }); return; }
      if (value.rootLength > 0) {
        await atomicJSON(job.health, { id, nonce: job.nonce, pid: process.pid, version: job.version, sourceTreeHash: job.sourceTreeHash, rootLength: value.rootLength });
        return;
      }
      await delay(200);
    }
    await atomicJSON(observation, { stage, nonempty: false });
  } catch { await atomicJSON(observation, { stage, error: true }).catch(() => {}); }
}
module.exports = { runHelper, readJob, acknowledge, terminalRecovery };
