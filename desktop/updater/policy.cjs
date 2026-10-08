const REPOSITORY = 'MrLaoGe/x2Stock';
const API = `https://api.github.com/repos/${REPOSITORY}`;
const MAX_DOWNLOAD = 512 * 1024 * 1024;

function fail(code) { const error = new Error(code); error.code = code; throw error; }
function semver(input) {
  if (typeof input !== 'string' || input.length > 128) return null;
  const m = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/.exec(input);
  if (!m) return null;
  const numbers = m.slice(1, 4).map(Number);
  const pre = m[4] ? m[4].split('.') : [];
  if (numbers.some((n) => !Number.isSafeInteger(n)) || pre.some((n) => /^\d+$/.test(n) && (n.length > 1 && n[0] === '0' || !Number.isSafeInteger(Number(n))))) return null;
  return { numbers, pre, value: input };
}
function compare(a, b) {
  a = typeof a === 'string' ? semver(a) : a; b = typeof b === 'string' ? semver(b) : b;
  if (!a || !b) fail('invalid-release');
  for (let i = 0; i < 3; i++) if (a.numbers[i] !== b.numbers[i]) return a.numbers[i] > b.numbers[i] ? 1 : -1;
  if (!a.pre.length || !b.pre.length) return a.pre.length === b.pre.length ? 0 : a.pre.length ? -1 : 1;
  for (let i = 0; i < Math.max(a.pre.length, b.pre.length); i++) {
    if (a.pre[i] === undefined || b.pre[i] === undefined) return a.pre[i] === undefined ? -1 : 1;
    if (a.pre[i] === b.pre[i]) continue;
    const an = /^\d+$/.test(a.pre[i]); const bn = /^\d+$/.test(b.pre[i]);
    if (an && bn) return Number(a.pre[i]) > Number(b.pre[i]) ? 1 : -1;
    if (an !== bn) return an ? -1 : 1;
    return a.pre[i] > b.pre[i] ? 1 : -1;
  }
  return 0;
}
function assertURL(input, kind = 'api') {
  let u; try { u = new URL(input); } catch { fail('invalid-release'); }
  if (u.protocol !== 'https:' || u.username || u.password || u.port || u.hash) fail('invalid-release');
  if (kind === 'api') {
    if (u.origin !== 'https://api.github.com' || !u.pathname.startsWith(`/repos/${REPOSITORY}/`)) fail('invalid-release');
  } else if (kind === 'asset') {
    if (u.origin !== 'https://github.com' || !u.pathname.startsWith(`/${REPOSITORY}/releases/download/`) || u.search) fail('invalid-release');
  } else if (kind === 'redirect') {
    if (!['release-assets.githubusercontent.com', 'objects.githubusercontent.com'].includes(u.hostname)) fail('invalid-release');
  } else if (kind === 'archive') {
    if (u.origin !== 'https://codeload.github.com' || !new RegExp(`^/${REPOSITORY}/zip/[a-f0-9]{40}$`).test(u.pathname) || u.search) fail('invalid-release');
  } else fail('invalid-release');
  return u;
}
function selectRelease(releases, currentVersion, now = Date.now()) {
  if (!Array.isArray(releases) || !semver(currentVersion)) fail('invalid-release');
  const possible = [];
  for (const release of releases) {
    if (!release || release.draft !== false || release.prerelease !== true || !Number.isSafeInteger(release.id) || release.id <= 0) continue;
    const tag = release.tag_name;
    const version = typeof tag === 'string' ? tag.replace(/^v/, '') : '';
    const parsed = semver(version);
    const published = Date.parse(release.published_at);
    if (!parsed || parsed.numbers[0] !== 0 || compare(parsed, currentVersion) <= 0 || !Number.isFinite(published) || published > now) continue;
    if (!Array.isArray(release.assets)) continue;
    const expectedName = `x2Stock-${version}-update.json`;
    if (release.assets.filter((asset) => typeof asset?.name === 'string' && asset.name.startsWith('x2Stock-') && asset.name.endsWith('-update.json')).length !== 1) continue;
    const archives = release.assets.filter((a) => a.name === expectedName && a.state === 'uploaded');
    if (archives.length !== 1) continue;
    const archive = archives[0];
    if (!Number.isSafeInteger(archive.id) || archive.id <= 0 || !Number.isSafeInteger(archive.size) || archive.size <= 0 || archive.size > 16384) continue;
    try { assertURL(archive.browser_download_url, 'asset'); } catch { continue; }
    const expectedPath = `/${REPOSITORY}/releases/download/${encodeURIComponent(tag)}/${encodeURIComponent(expectedName)}`;
    if (new URL(archive.browser_download_url).pathname !== expectedPath) continue;
    const digest = /^sha256:[a-fA-F0-9]{64}$/.test(archive.digest ?? '') ? archive.digest.slice(7).toLowerCase() : null;
    const sidecars = release.assets.filter((a) => a.name === `${expectedName}.sha256` && a.state === 'uploaded' && a.size > 0 && a.size <= 16384);
    let sidecar = sidecars.length === 1 ? sidecars[0] : null;
    if (sidecar) {
      try { assertURL(sidecar.browser_download_url, 'asset'); } catch { sidecar = null; }
      if (sidecar && new URL(sidecar.browser_download_url).pathname !== `${expectedPath}.sha256`) sidecar = null;
    }
    // This metadata authenticates the official source archive: require GitHub's
    // SHA-256 digest, rather than accepting a checksum file alone as metadata.
    if (!digest) continue;
    possible.push({ releaseId: release.id, version, tag, notes: String(release.body ?? '').slice(0, 32768), publishedAt: release.published_at, sizeBytes: archive.size, archive, sidecar, digest });
  }
  possible.sort((a, b) => compare(b.version, a.version) || b.releaseId - a.releaseId);
  return possible[0] ?? null;
}
function validateMetadata(value, candidate, sourceSha) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).sort().join(',') !== 'archive_sha256,archive_size,archive_url,repository,runtime_subdir,schema,source_sha,source_tree_hash,version') fail('invalid-release');
  if (!value || value.schema !== 1 || value.repository !== REPOSITORY || value.version !== candidate.version || value.source_sha !== sourceSha || value.runtime_subdir !== 'desktop-runtime/win-x64' || !/^[a-f0-9]{64}$/.test(value.source_tree_hash ?? '') || !/^[a-f0-9]{64}$/.test(value.archive_sha256 ?? '') || !Number.isSafeInteger(value.archive_size) || value.archive_size <= 0 || value.archive_size > MAX_DOWNLOAD) fail('invalid-release');
  assertURL(value.archive_url, 'archive');
  if (value.archive_url !== `https://codeload.github.com/${REPOSITORY}/zip/${sourceSha}`) fail('invalid-release');
  return value;
}
function parseChecksum(text, name) {
  const lines = text.trim().split(/\r?\n/);
  const matching = lines.map((line) => /^([a-fA-F0-9]{64})[ \t]+\*?(.+)$/.exec(line)).filter((m) => m && m[2] === name);
  if (matching.length !== 1) fail('hash');
  return matching[0][1].toLowerCase();
}
function publicCandidate(c) {
  if (!c) return undefined;
  return { releaseId: c.releaseId, version: c.version, notes: c.notes, publishedAt: c.publishedAt, sizeBytes: c.sizeBytes };
}
function validInstall(payload, candidate) {
  return payload && typeof payload === 'object' && Object.keys(payload).sort().join(',') === 'confirmed,releaseId,version' && payload.confirmed === true && payload.releaseId === candidate?.releaseId && payload.version === candidate?.version;
}
module.exports = { REPOSITORY, API, MAX_DOWNLOAD, fail, semver, compare, assertURL, selectRelease, validateMetadata, parseChecksum, publicCandidate, validInstall };
