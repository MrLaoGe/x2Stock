// Explicit local test realm only; ordinary startup never changes its instance domain.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
function child(parent, candidate) {
  const relative = path.relative(parent.toLowerCase(), candidate.toLowerCase());
  return relative !== '' && relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}
function fixtureAppData({ env = process.env, executable = process.execPath, temporary = os.tmpdir() } = {}) {
  if (!env.X2STOCK_TEST_REALM && !env.X2STOCK_TEST_NONCE) return null;
  if (!/^[a-f0-9]{64}$/.test(env.X2STOCK_TEST_NONCE ?? '') || !path.isAbsolute(env.X2STOCK_TEST_REALM ?? '')) throw new Error('Invalid test realm');
  const root = fs.realpathSync.native(env.X2STOCK_TEST_REALM);
  const temp = fs.realpathSync.native(temporary);
  if (!child(temp, root) || !path.basename(root).startsWith('x2stock-fixture-') || !child(root, fs.realpathSync.native(executable))) throw new Error('Invalid test containment');
  const markerFile = path.join(root, '.x2stock-test-fixture.json');
  const markerStat = fs.lstatSync(markerFile);
  if (!markerStat.isFile() || markerStat.isSymbolicLink() || markerStat.size > 1024) throw new Error('Invalid test marker');
  const marker = JSON.parse(fs.readFileSync(markerFile, 'utf8'));
  if (marker.schema !== 1 || marker.nonce !== env.X2STOCK_TEST_NONCE || fs.realpathSync.native(marker.root).toLowerCase() !== root.toLowerCase()) throw new Error('Invalid test marker');
  const data = path.join(root, 'state', 'appdata');
  fs.mkdirSync(data, { recursive: true });
  if (!child(root, fs.realpathSync.native(data))) throw new Error('Invalid test data');
  return data;
}
module.exports = { fixtureAppData };
