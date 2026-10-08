const fs = require('./raw-fs.cjs');
const crypto = require('node:crypto');
const { once } = require('node:events');
const { API, assertURL, fail } = require('./policy.cjs');
let fixtureOffline = false;
function setFixtureOffline(value) { fixtureOffline = value === true; }

async function request(url, { kind = 'api', limit = 2 * 1024 * 1024, timeout = 30000, file, expectedSize, progress, fetchImpl = fetch } = {}) {
  assertURL(url, kind);
  if (fixtureOffline) fail('network');
  let response;
  const signal = AbortSignal.timeout(timeout);
  try {
    for (let redirects = 0; redirects <= 4; redirects++) {
      response = await fetchImpl(url, { method: 'GET', redirect: 'manual', signal, headers: { Accept: kind === 'api' ? 'application/vnd.github+json' : 'application/octet-stream', 'User-Agent': 'x2Stock-update', 'X-GitHub-Api-Version': '2022-11-28' } });
      if (![301, 302, 303, 307, 308].includes(response.status)) break;
      await response.body?.cancel();
      const location = response.headers.get('location');
      if (!location || redirects === 4 || kind === 'api') fail('network');
      const next = new URL(location, url).href;
      assertURL(next, kind === 'archive' ? 'archive' : 'redirect'); url = next;
    }
    if (!response.ok || !response.body) fail('network');
    const contentLength = Number(response.headers.get('content-length'));
    if (contentLength && (!Number.isSafeInteger(contentLength) || contentLength > limit || expectedSize !== undefined && contentLength !== expectedSize)) fail('download');
    const hash = crypto.createHash('sha256');
    const chunks = [];
    let total = 0;
    const output = file ? fs.createWriteStream(file, { flags: 'wx' }) : null;
    let outputError;
    output?.on('error', (error) => { outputError = error; });
    try {
      for await (const chunk of response.body) {
        total += chunk.length;
        if (total > limit || expectedSize !== undefined && total > expectedSize) fail('download');
        hash.update(chunk);
        if (output) { if (outputError) throw outputError; if (!output.write(chunk)) await once(output, 'drain'); }
        else chunks.push(Buffer.from(chunk));
        progress?.(total);
      }
      if (expectedSize !== undefined && total !== expectedSize) fail('download');
      if (output) { output.end(); await once(output, 'finish'); }
      return { body: file ? undefined : Buffer.concat(chunks), digest: hash.digest('hex'), size: total };
    } finally { if (output && !output.closed) output.destroy(); }
  } catch (error) { if (error.code && ['download', 'invalid-release'].includes(error.code)) throw error; fail('network'); }
}
async function json(url, options) {
  const result = await request(url, options);
  try { return JSON.parse(result.body.toString('utf8')); } catch { fail('invalid-release'); }
}
async function releases() {
  const all = [];
  for (let page = 1; page <= 3; page++) {
    const entries = await json(`${API}/releases?per_page=100&page=${page}`);
    if (!Array.isArray(entries)) fail('invalid-release');
    all.push(...entries);
    if (entries.length < 100) break;
  }
  return all;
}
async function tagCommit(tag) {
  let ref = await json(`${API}/git/ref/tags/${encodeURIComponent(tag)}`);
  let object = ref.object;
  for (let i = 0; i < 4; i++) {
    if (!object || !/^[a-f0-9]{40}$/.test(object.sha)) fail('invalid-release');
    if (object.type === 'commit') return object.sha;
    if (object.type !== 'tag') fail('invalid-release');
    ref = await json(`${API}/git/tags/${object.sha}`); object = ref.object;
  }
  fail('invalid-release');
}
module.exports = { request, json, releases, tagCommit, setFixtureOffline };
