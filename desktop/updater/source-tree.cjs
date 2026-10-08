const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');

function isSourceFile(file) {
  return (file === 'VERSION' || /^(frontend|desktop)\//.test(file)) &&
    !file.split('/').some((part) => ['node_modules', 'dist', 'release', 'renderer', 'build', '__pycache__'].includes(part)) &&
    !/\.(pyc|tsbuildinfo)$/.test(file);
}
function hashSourceList(files) {
  const hash = crypto.createHash('sha256');
  for (const file of Object.keys(files).sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)))) hash.update(`${files[file]}  ${file}\n`, 'utf8');
  return hash.digest('hex');
}
async function sourceTree(repository) {
  const git = (args) => execFileSync('git', args, { cwd: repository, maxBuffer: 64 * 1024 * 1024 });
  git(['diff', '--quiet', 'HEAD', '--', 'frontend', 'desktop', 'VERSION']);
  const untracked = git(['ls-files', '--others', '--exclude-standard', '-z', '--', 'frontend', 'desktop', 'VERSION']).toString('utf8').split('\0').filter(isSourceFile);
  if (untracked.length) throw new Error('Untracked source files: clean commit required');
  const entries = git(['ls-files', '--stage', '-z', '--', 'frontend', 'desktop', 'VERSION']).toString('utf8').split('\0').filter(Boolean);
  const hashes = {};
  for (const entry of entries) {
    const match = /^(\d+) ([a-f0-9]{40,64}) (\d)\t(.+)$/.exec(entry);
    if (!match) throw new Error('Invalid Git index');
    const [, mode, oid, stage, file] = match;
    if (!isSourceFile(file)) continue;
    if (stage !== '0' || !['100644', '100755'].includes(mode)) throw new Error('Source must be regular tracked files');
    hashes[file] = crypto.createHash('sha256').update(git(['cat-file', 'blob', oid])).digest('hex');
  }
  return hashSourceList(hashes);
}
module.exports = { isSourceFile, hashSourceList, sourceTree };
