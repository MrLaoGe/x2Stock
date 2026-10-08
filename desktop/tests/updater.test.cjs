const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const { semver, compare, selectRelease, assertURL, parseChecksum, validateMetadata, validInstall } = require('../updater/policy.cjs');
const { request } = require('../updater/network.cjs');
const { safeEntry, extract, validateBundle, treeHashes, validateTree } = require('../updater/archive.cjs');
const { performSwap, recoverSwap, assertLayout } = require('../updater/apply.cjs');
const { validSender, registerIPC, UpdateController } = require('../updater/controller.cjs');
const { hashSourceList } = require('../updater/source-tree.cjs');
const SHA = 'a'.repeat(40); const HASH = 'b'.repeat(64); const ID = '12345678-1234-1234-1234-123456789012';
const digest = (body) => crypto.createHash('sha256').update(body).digest('hex');
function release(version, changes = {}) {
  const name = `x2Stock-${version}-update.json`;
  return { id: 1, tag_name: `v${version}`, draft: false, prerelease: true, published_at: '2026-01-01T00:00:00Z', body: 'synthetic notes', assets: [{ id: 2, name, state: 'uploaded', size: 100, digest: `sha256:${HASH}`, browser_download_url: `https://github.com/MrLaoGe/x2Stock/releases/download/v${version}/${name}` }], ...changes };
}
test('canonical integer SemVer ordering and cutoff reject aliases/leading zero/unsafe/future/draft/stable 0.x', () => {
  for (const value of ['0.01.0', 'v0.1.0', '0.1', '0.1.0-01', '9007199254740992.0.0']) assert.equal(semver(value), null);
  assert.equal(compare('0.2.0-beta.10', '0.2.0-beta.2'), 1);
  assert.equal(compare('0.2.0', '0.2.0-beta.10'), 1);
  assert.equal(compare('0.2.0+one', '0.2.0+two'), 0);
  assert.equal(selectRelease([release('0.3.0'), release('0.2.0')], '0.1.0').version, '0.3.0');
  for (const changes of [{ draft: true }, { prerelease: false }, { published_at: '2999-01-01' }, { assets: [] }]) assert.equal(selectRelease([release('0.2.0', changes)], '0.1.0'), null);
  assert.equal(selectRelease([release('0.1.0'), release('1.0.0')], '0.1.0'), null);
});
test('pinned origins, tag-bound metadata and strict install consent reject renderer URLs/tokens/paths', () => {
  for (const url of ['http://api.github.com/repos/MrLaoGe/x2Stock/releases', 'https://evil.test/repos/MrLaoGe/x2Stock/releases', 'https://token@api.github.com/repos/MrLaoGe/x2Stock/releases', 'https://api.github.com/repos/MrLaoGe/x2StockX/releases']) assert.throws(() => assertURL(url));
  assert.throws(() => assertURL('https://github.com/MrLaoGe/XXStock/releases/download/v0.2.0/a.zip', 'asset'));
  assert.throws(() => assertURL(`https://codeload.github.com/MrLaoGe/x2Stock/zip/${SHA}?` + ['token', 'example'].join('='), 'archive'));
  const candidate = { releaseId: 1, version: '0.2.0' };
  const valid = { releaseId: 1, version: '0.2.0', confirmed: true };
  assert.equal(validInstall(valid, candidate), true);
  for (const value of [{ ...valid, url: 'https://evil.test' }, { ...valid, confirmed: false }, { ...valid, releaseId: 2 }]) assert.equal(validInstall(value, candidate), false);
  const metadata = { schema: 1, repository: 'MrLaoGe/x2Stock', version: candidate.version, source_sha: SHA, runtime_subdir: 'desktop-runtime/win-x64', source_tree_hash: HASH, archive_sha256: HASH, archive_size: 123, archive_url: `https://codeload.github.com/MrLaoGe/x2Stock/zip/${SHA}` };
  assert.equal(validateMetadata(metadata, candidate, SHA), metadata);
  for (const changes of [{ source_sha: 'c'.repeat(40) }, { repository: 'other/repo' }, { runtime_subdir: '.env' }, { archive_size: 513 * 1024 * 1024 }, { extra: 'refuse unknown data' }]) assert.throws(() => validateMetadata({ ...metadata, ...changes }, candidate, SHA));
});
test('no eligible assets/digest/ambiguous asset never invents an update; checksum exact filename', () => {
  const absent = release('0.2.0'); absent.assets[0].digest = null;
  assert.equal(selectRelease([absent], '0.1.0'), null);
  const duplicate = release('0.2.0'); duplicate.assets.push(duplicate.assets[0]);
  assert.equal(selectRelease([duplicate], '0.1.0'), null);
  const otherVersion = release('0.2.0'); otherVersion.assets.push({ ...otherVersion.assets[0], name: 'x2Stock-0.3.0-update.json' });
  assert.equal(selectRelease([otherVersion], '0.1.0'), null);
  assert.equal(parseChecksum(`${HASH}  sample.zip\n`, 'sample.zip'), HASH);
  assert.throws(() => parseChecksum(`${HASH}  other.zip`, 'sample.zip'));
  assert.throws(() => parseChecksum(`${HASH}  sample.zip\n${HASH}  sample.zip`, 'sample.zip'));
});
test('bounded HTTP streaming handles digest, too-large/truncated payload, foreign redirect and offline without leaking details', async () => {
  const url = 'https://api.github.com/repos/MrLaoGe/x2Stock/releases';
  const result = await request(url, { limit: 5, expectedSize: 3, fetchImpl: async () => new Response('abc') });
  assert.equal(result.digest, digest('abc'));
  await assert.rejects(request(url, { limit: 2, fetchImpl: async () => new Response('abc') }), { code: 'download' });
  await assert.rejects(request(url, { expectedSize: 4, fetchImpl: async () => new Response('abc') }), { code: 'download' });
  await assert.rejects(request('https://github.com/MrLaoGe/x2Stock/releases/download/v0.2.0/a.zip', { kind: 'asset', fetchImpl: async () => new Response(null, { status: 302, headers: { location: 'https://evil.test/private-token' } }) }), { code: 'invalid-release' });
  await assert.rejects(request(url, { fetchImpl: async () => { throw new Error('private-token'); } }), (error) => error.message === 'network');
});
function zipFixture(entries) {
  const locals = []; const centrals = []; let offset = 0;
  for (const [name, raw, attributes = 0] of entries) {
    const body = Buffer.from(raw); const n = Buffer.from(name); const crc = zlib.crc32(body);
    const local = Buffer.alloc(30); local.writeUInt32LE(0x04034b50); local.writeUInt16LE(20, 4); local.writeUInt32LE(crc, 14); local.writeUInt32LE(body.length, 18); local.writeUInt32LE(body.length, 22); local.writeUInt16LE(n.length, 26);
    const central = Buffer.alloc(46); central.writeUInt32LE(0x02014b50); central.writeUInt16LE(0x314, 4); central.writeUInt16LE(20, 6); central.writeUInt32LE(crc, 16); central.writeUInt32LE(body.length, 20); central.writeUInt32LE(body.length, 24); central.writeUInt16LE(n.length, 28); central.writeUInt32LE(attributes >>> 0, 38); central.writeUInt32LE(offset, 42);
    locals.push(local, n, body); centrals.push(central, n); offset += local.length + n.length + body.length;
  }
  const cd = Buffer.concat(centrals); const end = Buffer.alloc(22); end.writeUInt32LE(0x06054b50); end.writeUInt16LE(entries.length, 8); end.writeUInt16LE(entries.length, 10); end.writeUInt32LE(cd.length, 12); end.writeUInt32LE(offset, 16);
  return Buffer.concat([...locals, cd, end]);
}
async function temporary(t) { const dir = require('node:fs').realpathSync.native(await fs.mkdtemp(path.join(os.tmpdir(), 'x2stock-update-test-'))); t.after(() => fs.rm(dir, { recursive: true, force: true })); return dir; }
test('archive rejects Windows traversal/ADS/device/case collision/symlink/CRC corruption', async (t) => {
  for (const name of ['../escape', 'C:/escape', '/absolute', 'a\\b', 'a:b', 'CON.txt', 'a/../b', 'a./b', 'a /b', 'a\0b']) assert.throws(() => safeEntry(name));
  const dir = await temporary(t);
  const bad = [zipFixture([['../outside', 'bad']]), zipFixture([['a.txt', 'a'], ['A.TXT', 'b']]), zipFixture([['link', 'a', 0xa1ff0000]])];
  const corrupt = zipFixture([['a.txt', 'abc']]); corrupt[35] ^= 1; bad.push(corrupt);
  for (let i = 0; i < bad.length; i++) { const zip = path.join(dir, `${i}.zip`); await fs.writeFile(zip, bad[i]); await assert.rejects(extract(zip, path.join(dir, `out${i}`))); }
  assert.equal(await fs.stat(path.join(dir, 'outside')).catch(() => null), null);
});
function bundleEntries(version, sourceTreeHash = HASH) {
  const pe = Buffer.alloc(128); pe.write('MZ'); pe.writeUInt32LE(64, 60); pe.write('PE\0\0', 64); pe.writeUInt16LE(0x8664, 68);
  return require('../updater/archive.cjs').RUNTIME_FILES.map((file) => [file, file === 'x2Stock.exe' ? pe : file === 'resources/build-manifest.json' ? JSON.stringify({ schema: 1, repository: 'MrLaoGe/x2Stock', version, build_source_sha: SHA, source_tree_hash: sourceTreeHash, platform: 'win32', arch: 'x64' }) : 'synthetic data']);
}
async function writeBundle(root, version) { for (const [file, data] of bundleEntries(version)) { await fs.mkdir(path.dirname(path.join(root, file)), { recursive: true }); await fs.writeFile(path.join(root, file), data); } }
test('full official source archive extracts runtime only, validates source tree/x64/manifest, retains project/private/data', async (t) => {
  const dir = await temporary(t); const prefix = `x2Stock-${SHA}/`;
  const source = { VERSION: digest('0.2.0'), 'frontend/src/example.ts': digest('synthetic') };
  const sourceHash = hashSourceList(source);
  const entries = [[`${prefix}VERSION`, '0.2.0'], [`${prefix}frontend/src/example.ts`, 'synthetic'], [`${prefix}.env`, 'never extract'], ...bundleEntries('0.2.0', sourceHash).map(([name, body]) => [`${prefix}desktop-runtime/win-x64/${name}`, body])];
  const zip = path.join(dir, 'full.zip'); await fs.writeFile(zip, zipFixture(entries));
  const runtime = path.join(dir, 'runtime'); await extract(zip, runtime, { runtimeOnly: true, sourceTreeHash: sourceHash, sourceSha: SHA });
  await validateBundle(runtime, { version: '0.2.0', sourceTreeHash: sourceHash });
  assert.equal(await fs.stat(path.join(runtime, '.env')).catch(() => null), null);
  await assert.rejects(validateBundle(runtime, { version: '0.3.0', sourceTreeHash: sourceHash }), { code: 'bundle' });
  await assert.rejects(extract(zip, path.join(dir, 'wronghash'), { runtimeOnly: true, sourceTreeHash: HASH, sourceSha: SHA }), { code: 'archive' });
  await assert.rejects(extract(zip, path.join(dir, 'wrongcommit'), { runtimeOnly: true, sourceTreeHash: sourceHash, sourceSha: 'c'.repeat(40) }), { code: 'archive' });
});
test('strict 73-file runtime rejects each missing file, unknown private files and unmaterialized LFS', async (t) => {
  const root = await temporary(t); await writeBundle(root, '0.2.0');
  const options = { version: '0.2.0', sourceTreeHash: HASH };
  await validateBundle(root, options);
  for (const relative of require('../updater/archive.cjs').RUNTIME_FILES) {
    const file = path.join(root, relative); const original = await fs.readFile(file); await fs.unlink(file);
    await assert.rejects(validateBundle(root, options), { code: 'bundle' }); await fs.writeFile(file, original);
  }
  await fs.writeFile(path.join(root, 'personal.sqlite'), 'private');
  await assert.rejects(validateBundle(root, options), { code: 'bundle' }); await fs.unlink(path.join(root, 'personal.sqlite'));
  await fs.writeFile(path.join(root, 'ffmpeg.dll'), 'version https://git-lfs.github.com/spec/v1\noid sha256:synthetic');
  await assert.rejects(validateBundle(root, options), { code: 'bundle' });
});
async function swapJob(t) {
  const root = await temporary(t); const appData = path.join(root, 'appdata'); const updates = path.join(appData, 'x2Stock', 'updates');
  const target = path.join(root, 'project', 'desktop-runtime', 'win-x64');
  const next = path.join(path.dirname(target), `.x2stock-next-${ID}`); const backup = path.join(path.dirname(target), `.x2stock-backup-${ID}`);
  await writeBundle(target, '0.1.0'); await writeBundle(next, '0.2.0');
  const jobRoot = path.join(updates, 'jobs', ID);
  const job = { schema: 1, repository: 'MrLaoGe/x2Stock', id: ID, jobRoot, helper: path.join(jobRoot, 'helper'), health: path.join(jobRoot, 'health.json'), nonce: HASH, parentPID: 123, target, next, backup, version: '0.2.0', sourceSha: SHA, sourceTreeHash: HASH, hashes: await treeHashes(next), previousHashes: await treeHashes(target) };
  assertLayout(job, updates, appData);
  const data = path.join(appData, 'XXStock', 'profile', 'language.txt'); await fs.mkdir(path.dirname(data), { recursive: true }); await fs.writeFile(data, 'en');
  const env = path.join(root, 'project', '.env'); await fs.writeFile(env, 'synthetic');
  return { job, updates, appData, data, env };
}
test('helper transaction succeeds only on health, preserving backup/project/data', async (t) => {
  const { job, data, env } = await swapJob(t); const phases = [];
  assert.equal(await performSwap(job, { journal: async (phase) => phases.push(phase), launch: async () => ({}), waitHealthy: async () => true, stop: async () => {} }), 'healthy');
  await validateTree(job.target, job.hashes); await validateTree(job.backup, job.previousHashes);
  assert.deepEqual(phases, ['backing-up', 'backed-up', 'awaiting-health', 'healthy']);
  assert.equal(await fs.readFile(data, 'utf8'), 'en'); assert.equal(await fs.readFile(env, 'utf8'), 'synthetic');
});
for (const fault of ['second-rename', 'launch', 'health']) test(`helper rollback on ${fault} retains usable old bundle/data`, async (t) => {
  const { job, data, env } = await swapJob(t); let renames = 0; let launches = 0;
  const result = await performSwap(job, { journal: async () => {}, rename: async (a, b) => { if (++renames === 2 && fault === 'second-rename') throw new Error('fault'); await fs.rename(a, b); }, launch: async () => { if (++launches === 1 && fault === 'launch') throw new Error('fault'); return {}; }, waitHealthy: async () => fault !== 'health', stop: async () => {} });
  assert.equal(result, 'rolled-back'); await validateTree(job.target, job.previousHashes);
  assert.equal(await fs.readFile(data, 'utf8'), 'en'); assert.equal(await fs.readFile(env, 'utf8'), 'synthetic');
});
test('interrupted first directory rename recovers old runtime; post-stage tamper and data-root target refused', async (t) => {
  const { job, appData, updates } = await swapJob(t);
  await fs.rename(job.target, job.backup);
  assert.equal(await recoverSwap(job, async () => {}, async () => ({})), true);
  await validateTree(job.target, job.previousHashes);
  await fs.writeFile(path.join(job.next, 'x2Stock.exe'), 'tampered');
  await assert.rejects(performSwap(job, { journal: async () => {}, launch: async () => ({}), waitHealthy: async () => true, stop: async () => {} }), { code: 'hash' });
  assert.throws(() => assertLayout({ ...job, target: path.join(appData, 'desktop-runtime', 'win-x64') }, updates, appData));
});
test('IPC allowlist rejects subframes, external/unowned senders, extra args and never exposes paths', async () => {
  const frame = { url: 'file:///C:/app/index.html#/style-preview' }; const contents = { mainFrame: frame };
  const win = { isDestroyed: () => false, webContents: contents };
  const event = { sender: contents, senderFrame: frame };
  assert.equal(validSender(event, win, 'file:///C:/app/index.html'), true);
  assert.equal(validSender({ ...event, senderFrame: { url: frame.url } }, win, 'file:///C:/app/index.html'), false);
  frame.url = 'https://evil.test'; assert.equal(validSender(event, win, 'file:///C:/app/index.html'), false); frame.url = 'file:///C:/app/index.html';
  const handlers = new Map(); const controller = new UpdateController({ app: {}, metadata: { version: '0.1.0' } });
  registerIPC({ ipcMain: { handle: (channel, handler) => handlers.set(channel, handler) }, controller, getWindow: () => win, rendererURL: frame.url });
  assert.equal(handlers.size, 3);
  const value = await handlers.get('x2stock:update:check')(event, 'https://evil.test');
  assert.equal(value.errorCode, 'ipc'); assert.equal(JSON.stringify(value).includes('C:/'), false);
  assert.equal((await controller.install({})).errorCode, 'ipc');
});
test('busy install cannot remove another updater lock; revisions increase and snapshots cannot mutate state', async (t) => {
  const root = await temporary(t);
  const controller = new UpdateController({ app: {}, metadata: { version: '0.1.0' }, updatesRoot: path.join(root, 'updates') });
  const initial = controller.getStatus(); initial.phase = 'applying';
  assert.equal(controller.getStatus().phase, 'idle');
  controller.set('downloading');
  const busy = await controller.install({ confirmed: true });
  assert.equal(busy.busy, true); assert.equal(busy.phase, 'downloading');
  assert.ok(busy.revision > initial.revision);
  await fs.mkdir(controller.updatesRoot); const file = path.join(controller.updatesRoot, 'update.lock');
  await fs.writeFile(file, JSON.stringify({ parentPID: process.pid }));
  await controller.restoreResult();
  assert.ok(await fs.stat(file));
});
test('fixture realm only enables for a marked temp runtime copy with exact nonce, preserving default app', async (t) => {
  const { fixtureAppData } = require('../updater/fixture.cjs');
  assert.equal(fixtureAppData({ env: {} }), null);
  const parent = await temporary(t); const root = path.join(parent, 'x2stock-fixture-test'); await fs.mkdir(root);
  const executable = path.join(root, 'x2Stock.exe'); await fs.writeFile(executable, 'synthetic');
  const env = { X2STOCK_TEST_REALM: root, X2STOCK_TEST_NONCE: HASH };
  assert.throws(() => fixtureAppData({ env, executable, temporary: parent }));
  await fs.writeFile(path.join(root, '.x2stock-test-fixture.json'), JSON.stringify({ schema: 1, root, nonce: HASH }));
  assert.equal(fixtureAppData({ env, executable, temporary: parent }), path.join(root, 'state', 'appdata'));
  assert.throws(() => fixtureAppData({ env: { ...env, X2STOCK_TEST_NONCE: 'c'.repeat(64) }, executable, temporary: parent }));
  assert.throws(() => fixtureAppData({ env, executable: process.execPath, temporary: parent }));
  assert.throws(() => fixtureAppData({ env, executable, temporary: root }));
});
test('health acknowledgement binds local URL and manifest, waits for nonempty root, and refuses wrong URL/version/hash', async (t) => {
  const { job, updates, appData } = await swapJob(t);
  await fs.mkdir(job.jobRoot, { recursive: true });
  const file = path.join(job.jobRoot, 'job.json'); await fs.writeFile(file, JSON.stringify(job));
  await fs.writeFile(path.join(job.jobRoot, 'job.sha256'), await require('../updater/archive.cjs').hashFile(file));
  const renderer = path.join(job.target, 'resources', 'app.asar', 'renderer');
  const url = require('node:url').pathToFileURL(path.join(renderer, 'index.html')).href;
  let samples = 0;
  const window = { __rendererPath: renderer, isDestroyed: () => false, webContents: { executeJavaScript: async () => ({ url: `${url}#/style-preview`, rootLength: ++samples === 1 ? 0 : 10 }) } };
  const args = { id: job.id, updatesRoot: updates, appData, target: job.target, metadata: { version: job.version, source_tree_hash: job.sourceTreeHash }, window };
  const { acknowledge } = require('../updater/helper.cjs');
  await acknowledge(args);
  const ack = JSON.parse(await fs.readFile(job.health, 'utf8')); assert.equal(ack.rootLength, 10); assert.equal(ack.nonce, job.nonce); assert.equal(samples, 2);
  await fs.unlink(job.health);
  for (const changes of [{ metadata: { version: '0.9.0', source_tree_hash: job.sourceTreeHash } }, { metadata: { version: job.version, source_tree_hash: 'c'.repeat(64) } }, { window: { ...window, webContents: { executeJavaScript: async () => ({ url: 'https://evil.test', rootLength: 100 }) } } }]) {
    await acknowledge({ ...args, ...changes }); assert.equal(await fs.stat(job.health).catch(() => null), null);
  }
});
test('rollback-failed terminal recovery retries the verified backup and fails if nothing can restore', async (t) => {
  const { job } = await swapJob(t); await fs.rename(job.target, job.backup);
  let opened = 0; const { terminalRecovery } = require('../updater/helper.cjs');
  const options = { recovery: true, launch: async () => { opened++; }, restore: recoverSwap, journal: async () => {} };
  assert.equal(await terminalRecovery({ phase: 'rollback-failed' }, job, options), true);
  assert.equal(opened, 1); await validateTree(job.target, job.previousHashes);
  await assert.rejects(terminalRecovery({ phase: 'rollback-failed' }, job, { ...options, restore: async () => false }), { code: 'rollback' });
});
test('source identity uses clean canonical Git blobs across CRLF checkout and rejects dirty/untracked source', async (t) => {
  const root = await temporary(t); const git = (...args) => require('node:child_process').execFileSync('git', args, { cwd: root, stdio: ['ignore','pipe','pipe'] });
  git('init','--quiet'); git('config','user.name','Synthetic'); git('config','user.email','synthetic@example.invalid'); git('config','core.autocrlf','false');
  await fs.mkdir(path.join(root,'desktop')); await fs.writeFile(path.join(root,'.gitattributes'),'*.cjs text\n'); await fs.writeFile(path.join(root,'VERSION'),'0.1.0\n'); await fs.writeFile(path.join(root,'desktop','a.cjs'),'one\ntwo\n');
  git('add','.'); git('commit','--quiet','-m','synthetic');
  const { sourceTree } = require('../updater/source-tree.cjs'); const expected = await sourceTree(root);
  await fs.writeFile(path.join(root,'desktop','a.cjs'),'one\r\ntwo\r\n'); assert.equal(await sourceTree(root),expected);
  await fs.writeFile(path.join(root,'desktop','a.cjs'),'changed\n'); await assert.rejects(sourceTree(root));
  git('checkout','--','desktop/a.cjs'); await fs.writeFile(path.join(root,'desktop','untracked.cjs'),'new'); await assert.rejects(sourceTree(root));
});
