const fs = require('./raw-fs.cjs').promises;
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const { Transform } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { createReadStream, createWriteStream } = require('./raw-fs.cjs');
const yauzl = require('yauzl');
const { REPOSITORY, fail } = require('./policy.cjs');
const { isSourceFile, hashSourceList } = require('./source-tree.cjs');
const RUNTIME_FILES = require('./runtime-files.json');
const RUNTIME_SET = new Set(RUNTIME_FILES);

function safeEntry(name) {
  if (typeof name !== 'string' || !name || name !== name.normalize('NFC') || name.length > 240 || /[\\:\x00-\x1f]/.test(name) || name.startsWith('/')) fail('archive');
  const parts = name.replace(/\/$/, '').split('/');
  if (parts.some((part) => !part || part === '.' || part === '..' || /[. ]$/.test(part) || /[<>"|?*]/.test(part) || /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(part))) fail('archive');
  return parts.join('/');
}
function contained(parent, candidate) {
  const relative = path.relative(path.resolve(parent), path.resolve(candidate));
  return relative !== '' && relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}
async function hashFile(file) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
}
async function treeHashes(root) {
  const hashes = {};
  async function walk(directory) {
    const entries = await fs.readdir(directory, { withFileTypes: true });
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      const file = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) fail('bundle');
      if (entry.isDirectory()) await walk(file);
      else if (entry.isFile()) hashes[path.relative(root, file).split(path.sep).join('/')] = await hashFile(file);
      else fail('bundle');
    }
  }
  await walk(root); return hashes;
}
async function validateTree(root, expected) {
  const actual = await treeHashes(root);
  if (JSON.stringify(Object.entries(actual).sort()) !== JSON.stringify(Object.entries(expected).sort())) fail('hash');
}
async function extract(archive, destination, { runtimeOnly = false, sourceTreeHash, sourceSha } = {}) {
  await fs.mkdir(destination, { recursive: false });
  const zip = await new Promise((resolve, reject) => yauzl.open(archive, { lazyEntries: true, strictFileNames: true, validateEntrySizes: true }, (err, zip) => err ? reject(err) : resolve(zip)));
  const seen = new Set(); const sourceFiles = {}; let sourceBytes = 0; let count = 0; let expanded = 0; let archiveRoot;
  return new Promise((resolve, reject) => {
    let stopped = false;
    const abort = () => { if (!stopped) { stopped = true; zip.close(); const e = new Error('archive'); e.code = 'archive'; reject(e); } };
    zip.on('error', abort);
    zip.on('end', () => {
      if (runtimeOnly && hashSourceList(sourceFiles) !== sourceTreeHash) { abort(); return; }
      if (!stopped) { stopped = true; resolve(); }
    });
    zip.on('entry', async (entry) => {
      try {
        let relative = safeEntry(entry.fileName);
        const key = relative.normalize('NFC').toLowerCase();
        if (seen.has(key) || ++count > 5000 || entry.generalPurposeBitFlag & 1 || ![0, 8].includes(entry.compressionMethod)) fail('archive');
        seen.add(key);
        const type = (entry.externalFileAttributes >>> 16) & 0xf000;
        if (type && type !== 0x8000 && type !== 0x4000) fail('archive');
        expanded += entry.uncompressedSize;
        if (entry.uncompressedSize > 512 * 1024 * 1024 || expanded > 1200 * 1024 * 1024) fail('archive');
        if (runtimeOnly) {
          const parts = relative.split('/');
          if (!/^[a-f0-9]{40}$/.test(sourceSha ?? '') || parts[0] !== `x2Stock-${sourceSha}`) fail('archive');
          archiveRoot ??= parts[0];
          if (archiveRoot !== parts[0]) fail('archive');
          const sourceFile = parts.slice(1).join('/');
          if (!entry.fileName.endsWith('/') && isSourceFile(sourceFile)) {
            if (entry.uncompressedSize > 8 * 1024 * 1024 || (sourceBytes += entry.uncompressedSize) > 64 * 1024 * 1024) fail('archive');
            const input = await new Promise((r, j) => zip.openReadStream(entry, (e, s) => e ? j(e) : r(s)));
            const hash = crypto.createHash('sha256'); let crc = 0; let size = 0;
            for await (const chunk of input) { hash.update(chunk); crc = zlib.crc32(chunk, crc); size += chunk.length; }
            if (size !== entry.uncompressedSize || crc !== entry.crc32) fail('archive');
            sourceFiles[sourceFile] = hash.digest('hex');
          }
          if (parts[1] !== 'desktop-runtime' || parts[2] !== 'win-x64' || parts.length < 4) { zip.readEntry(); return; }
          relative = parts.slice(3).join('/');
          if (entry.fileName.endsWith('/') ? !RUNTIME_FILES.some((file) => file.startsWith(`${relative}/`)) : !RUNTIME_SET.has(relative)) fail('archive');
        }
        const target = path.join(destination, relative);
        if (!contained(destination, target)) fail('archive');
        if (entry.fileName.endsWith('/')) await fs.mkdir(target, { recursive: true });
        else {
          await fs.mkdir(path.dirname(target), { recursive: true });
          const input = await new Promise((r, j) => zip.openReadStream(entry, (e, s) => e ? j(e) : r(s)));
          let crc = 0; let size = 0;
          const counter = new Transform({ transform(chunk, encoding, callback) { size += chunk.length; crc = zlib.crc32(chunk, crc); callback(null, chunk); } });
          await pipeline(input, counter, createWriteStream(target, { flags: 'wx' }));
          if (size !== entry.uncompressedSize || crc !== entry.crc32) fail('archive');
        }
        if (!stopped) zip.readEntry();
      } catch { abort(); }
    });
    zip.readEntry();
  });
}
async function validateBundle(root, { version, sourceTreeHash }) {
  try {
    const files = Object.keys(await treeHashes(root)).sort();
    if (JSON.stringify(files) !== JSON.stringify([...RUNTIME_FILES].sort())) fail('bundle');
    const allowedDirectories = new Set(RUNTIME_FILES.filter((file) => file.includes('/')).map((file) => path.posix.dirname(file)));
    for (const entry of await fs.readdir(root, { withFileTypes: true })) {
      if (entry.isDirectory() && !allowedDirectories.has(entry.name)) fail('bundle');
    }
    for (const directory of allowedDirectories) {
      for (const entry of await fs.readdir(path.join(root, directory), { withFileTypes: true })) if (entry.isDirectory()) fail('bundle');
    }
    for (const relative of RUNTIME_FILES) {
      const handle = await fs.open(path.join(root, relative), 'r');
      try {
        const stat = await handle.stat(); const prefix = Buffer.alloc(128);
        await handle.read(prefix, 0, prefix.length, 0);
        if (!stat.size || prefix.toString('utf8').startsWith('version https://git-lfs.github.com/spec/v1')) fail('bundle');
      } finally { await handle.close(); }
    }
    const executable = path.join(root, 'x2Stock.exe');
    const handle = await fs.open(executable, 'r');
    try {
      const header = Buffer.alloc(64); await handle.read(header, 0, 64, 0);
      const peOffset = header.readUInt32LE(60);
      if (header.toString('ascii', 0, 2) !== 'MZ' || peOffset < 64 || peOffset > 1024 * 1024) fail('bundle');
      const pe = Buffer.alloc(6); await handle.read(pe, 0, 6, peOffset);
      if (pe.toString('ascii', 0, 4) !== 'PE\0\0' || pe.readUInt16LE(4) !== 0x8664) fail('bundle');
    } finally { await handle.close(); }
    for (const relative of ['resources/app.asar', 'icudtl.dat', 'resources.pak', 'chrome_100_percent.pak', 'v8_context_snapshot.bin']) {
      const stat = await fs.lstat(path.join(root, relative));
      if (!stat.isFile() || stat.isSymbolicLink() || !stat.size) fail('bundle');
    }
    const metadataFile = path.join(root, 'resources', 'build-manifest.json');
    const stat = await fs.lstat(metadataFile);
    if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 8192) fail('bundle');
    const metadata = JSON.parse(await fs.readFile(metadataFile, 'utf8'));
    if (Object.keys(metadata).sort().join(',') !== 'arch,build_source_sha,platform,repository,schema,source_tree_hash,version') fail('bundle');
    if (metadata.schema !== 1 || metadata.repository !== REPOSITORY || metadata.version !== version || !/^[a-f0-9]{40}$/.test(metadata.build_source_sha ?? '') || metadata.source_tree_hash !== sourceTreeHash || metadata.platform !== 'win32' || metadata.arch !== 'x64') fail('bundle');
    return metadata;
  } catch { fail('bundle'); }
}
module.exports = { RUNTIME_FILES, safeEntry, contained, hashFile, treeHashes, validateTree, extract, validateBundle };
