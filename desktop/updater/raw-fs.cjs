// Updater verifies/copies the physical ASAR bytes. Electron's patched fs treats
// ASAR archives as directories and must never be used for these operations.
module.exports = process.versions.electron ? require('original-fs') : require('node:fs');
