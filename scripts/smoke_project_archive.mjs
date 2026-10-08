// QA only: observe a packaged local renderer over the explicitly isolated CDP port.
import { setTimeout as delay } from 'node:timers/promises';

const port = Number(process.argv[2]);
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid local test port');
const base = `http://127.0.0.1:${port}`;
async function endpoint(name) {
  const response = await fetch(`${base}/${name}`, { signal: AbortSignal.timeout(2000) });
  if (!response.ok) throw new Error('Local CDP endpoint unavailable');
  return response.json();
}
async function channel(url) {
  const parsed = new URL(url);
  if (parsed.protocol !== 'ws:' || parsed.hostname !== '127.0.0.1' || Number(parsed.port) !== port) throw new Error('Nonlocal CDP target');
  const ws = new WebSocket(url);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('CDP connect deadline')), 5000);
    ws.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
    ws.addEventListener('error', () => { clearTimeout(timer); reject(new Error('CDP connect failed')); }, { once: true });
  });
  let sequence = 0;
  const pending = new Map();
  ws.addEventListener('message', (message) => {
    const value = JSON.parse(message.data);
    if (!pending.has(value.id)) return;
    const { resolve, reject, timer } = pending.get(value.id);
    pending.delete(value.id); clearTimeout(timer);
    if (value.error) reject(new Error('Local CDP command failed')); else resolve(value.result);
  });
  return {
    command(method, params = {}) {
      const id = ++sequence;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP command deadline')); }, 5000);
        pending.set(id, { resolve, reject, timer }); ws.send(JSON.stringify({ id, method, params }));
      });
    },
    close() { ws.close(); },
  };
}
let page;
let browser;
try {
  const targets = await endpoint('json/list');
  const target = targets.find((value) => value.type === 'page' && value.url.startsWith('file:') && value.url.includes('/resources/app.asar/renderer/index.html'));
  if (!target) throw new Error('Packaged local renderer missing');
  page = await channel(target.webSocketDebuggerUrl);
  browser = await channel((await endpoint('json/version')).webSocketDebuggerUrl);
  const commandLine = await browser.command('Browser.getBrowserCommandLine');
  if (!commandLine.arguments.some((arg) => arg.startsWith('--host-resolver-rules=') && arg.includes('MAP * ~NOTFOUND'))) throw new Error('Offline resolver rule is absent');
  const processes = await browser.command('SystemInfo.getProcessInfo');
  const pid = processes.processInfo.find((process) => process.type === 'browser')?.id;
  if (!Number.isSafeInteger(pid) || pid <= 0) throw new Error('Owned browser process missing');
  let observation;
  for (let attempt = 0; attempt < 100; attempt++) {
    const result = await page.command('Runtime.evaluate', {
      expression: '({rootLength:document.querySelector("#root")?.innerText.trim().length || 0,title:document.title,language:document.documentElement.lang,url:location.href,bridge:Boolean(window.x2stockDesktop?.updates)})',
      returnByValue: true,
    });
    if (result.exceptionDetails) throw new Error('Packaged renderer evaluation failed');
    observation = result.result.value;
    if (observation?.rootLength > 0) break;
    await delay(200);
  }
  if (!observation || observation.rootLength <= 0 || observation.language !== 'zh-CN' || !observation.bridge || !observation.title.includes('x2Stock')) throw new Error('Packaged default renderer acceptance failed');
  let updateStatus;
  for (let attempt = 0; attempt < 30; attempt++) {
    const result = await page.command('Runtime.evaluate', {
      expression: 'window.x2stockDesktop.updates.check()', awaitPromise: true, returnByValue: true,
    });
    if (result.exceptionDetails) throw new Error('Offline updater check failed');
    updateStatus = result.result.value;
    if (!updateStatus?.busy) break;
    await delay(200);
  }
  if (updateStatus?.phase !== 'error' || updateStatus.errorCode !== 'network') throw new Error('Isolated Node update network is not blocked');
  process.stdout.write(JSON.stringify({ ...observation, pid, offlineRulesVerified: true, offlineUpdaterVerified: true }));
} finally {
  page?.close(); browser?.close();
}
