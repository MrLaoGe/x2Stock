const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('x2stockDesktop', Object.freeze({
  platform: process.platform,
  arch: process.arch,
  version: '0.1.0-preview.1',
}));
