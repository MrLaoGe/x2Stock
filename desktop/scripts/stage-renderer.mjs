import { cp, mkdir, rm, readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import sourceTreeModule from '../updater/source-tree.cjs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const desktop = resolve(here, '..');
const source = resolve(desktop, '..', 'frontend', 'dist');
const target = resolve(desktop, 'renderer');
const repository = resolve(desktop, '..');
const sourceTreeHash = await sourceTreeModule.sourceTree(repository);

await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await cp(source, target, { recursive: true });
const version = (await readFile(resolve(repository, 'VERSION'), 'utf8')).trim();
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('Invalid root VERSION');
await mkdir(resolve(desktop, 'build'), { recursive: true });
await writeFile(resolve(desktop, 'build', 'build-manifest.json'), JSON.stringify({
  schema: 1, repository: 'MrLaoGe/x2Stock', version,
  build_source_sha: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository }).toString().trim(),
  source_tree_hash: sourceTreeHash, platform: 'win32', arch: 'x64',
}));
console.log(`staged renderer from ${source}`);
