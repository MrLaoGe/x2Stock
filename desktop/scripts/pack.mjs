import { readFile, unlink, lstat } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';
const desktop = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const version = (await readFile(resolve(desktop, '..', 'VERSION'), 'utf8')).trim();
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('Invalid root VERSION');
execFileSync(process.execPath, [resolve(desktop, 'scripts', 'stage-renderer.mjs')], { cwd: desktop, stdio: 'inherit' });
const args = [resolve(desktop, 'node_modules', 'electron-builder', 'cli.js'), '--win', 'dir', '--x64', '--publish', 'never', `--config.extraMetadata.version=${version}`];
if (process.env.X2STOCK_ELECTRON_DIST) args.push(`--config.electronDist=${resolve(process.env.X2STOCK_ELECTRON_DIST)}`);
execFileSync(process.execPath, args, { cwd: desktop, stdio: 'inherit' });
const output = resolve(desktop, 'release', 'win-unpacked');
// electron-builder custom-dist mode retains these two stock Electron templates.
// This is ignored build output, never an existing delivery or installed runtime.
for (const stock of ['resources/default_app.asar', 'version']) {
  const file = resolve(output, stock);
  try { const stat = await lstat(file); if (!stat.isFile() || stat.isSymbolicLink()) throw new Error('Invalid stock build template'); await unlink(file); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
}
const metadata = JSON.parse(await readFile(resolve(output, 'resources', 'build-manifest.json'), 'utf8'));
await createRequire(import.meta.url)('../updater/archive.cjs').validateBundle(output, { version, sourceTreeHash: metadata.source_tree_hash });
