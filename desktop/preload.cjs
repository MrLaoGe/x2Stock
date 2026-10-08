const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('x2stockDesktop', Object.freeze({
  platform: process.platform,
  arch: process.arch,
  version: process.argv.find((arg) => arg.startsWith('--x2stock-version='))?.split('=')[1] ?? '',
  updates: Object.freeze({
    getStatus: () => ipcRenderer.invoke('x2stock:update:status'),
    check: () => ipcRenderer.invoke('x2stock:update:check'),
    install: (request) => ipcRenderer.invoke('x2stock:update:install', request),
    onStatus: (listener) => {
      if (typeof listener !== 'function') throw new TypeError('Expected a status listener');
      const wrapped = (_event, status) => listener(status);
      ipcRenderer.on('x2stock:update:changed', wrapped);
      return () => ipcRenderer.removeListener('x2stock:update:changed', wrapped);
    },
  }),
}));
