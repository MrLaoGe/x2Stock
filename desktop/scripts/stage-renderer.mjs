import { cp, mkdir, rm } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const desktop = resolve(here, '..');
const source = resolve(desktop, '..', 'frontend', 'dist');
const target = resolve(desktop, 'renderer');

await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await cp(source, target, { recursive: true });
console.log(`staged renderer from ${source}`);
