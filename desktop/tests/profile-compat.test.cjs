const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'main.cjs'), 'utf8');

for (const legacyDirectory of [null, 'profile', 'session']) {
  test(`data paths preserve legacy ${legacyDirectory ?? 'absent'} installation`, () => {
    const parent = path.resolve('synthetic-app-data');
    const legacyRoot = path.join(parent, 'XXStock');
    const configured = new Map();
    const app = {
      getPath: () => parent,
      setPath: (name, value) => configured.set(name, value),
      whenReady: () => ({ then() {} }),
      on() {},
    };
    vm.runInNewContext(source, {
      __dirname: path.join(__dirname, '..'),
      process: { env: {}, platform: 'win32', argv: [], execPath: path.join(parent, 'desktop-runtime', 'win-x64', 'x2Stock.exe') },
      require(name) {
        if (name === 'electron') return { app };
        if (name === './updater/fixture.cjs') return { fixtureAppData: () => null };
        if (name === './updater/raw-fs.cjs') return { existsSync: () => false };
        if (name === './updater/recovery.cjs') return { pendingFile: () => 'synthetic-pending' };
        if (name === 'node:fs') return {
          existsSync: (candidate) => legacyDirectory !== null &&
            candidate === path.join(legacyRoot, legacyDirectory),
        };
        return require(name);
      },
    });
    const expectedRoot = legacyDirectory ? legacyRoot : path.join(parent, 'x2Stock');
    for (const [name, directory] of [
      ['userData', 'profile'], ['sessionData', 'session'],
      ['cache', 'cache'], ['downloads', 'downloads'],
    ]) assert.equal(configured.get(name), path.join(expectedRoot, directory));
  });
}
