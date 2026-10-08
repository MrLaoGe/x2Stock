import { test } from 'node:test'
import assert from 'node:assert/strict'
import { acceptUpdateStatus, installationRequest, isActiveUpdate } from '../src/update-state.ts'

const candidate = { releaseId: 17, version: '0.1.4', notes: '', publishedAt: '2026-10-08T00:00:00Z', sizeBytes: 1000 }
const available = { revision: 5, phase: 'available', busy: false, currentVersion: '0.1.3', candidate }

test('download is never authorized without explicit candidate confirmation', () => {
  assert.equal(installationRequest(available, null), null)
  assert.deepEqual(installationRequest(available, candidate), { releaseId: 17, version: '0.1.4', confirmed: true })
})
test('changed release/version, active operation, and terminal states invalidate consent', () => {
  assert.equal(installationRequest(available, { ...candidate, releaseId: 18 }), null)
  assert.equal(installationRequest(available, { ...candidate, version: '0.1.5' }), null)
  assert.equal(installationRequest({ ...available, busy: true }, candidate), null)
  for (const phase of ['idle', 'no-update', 'checking', 'error', 'applying']) {
    assert.equal(installationRequest({ ...available, phase }, candidate), null)
  }
})
test('slower IPC responses cannot regress the displayed update revision', () => {
  assert.equal(acceptUpdateStatus(available, { ...available, revision: 2, phase: 'checking' }), available)
  assert.equal(acceptUpdateStatus(null, available), available)
  assert.equal(acceptUpdateStatus(available, { ...available, revision: 6, phase: 'error' }).phase, 'error')
})
test('only ongoing phases or busy operations require polling', () => {
  for (const phase of ['checking', 'downloading', 'verifying', 'staged', 'applying']) assert.equal(isActiveUpdate({ ...available, phase }), true)
  for (const phase of ['idle', 'available', 'no-update', 'error']) assert.equal(isActiveUpdate({ ...available, phase }), false)
  assert.equal(isActiveUpdate({ ...available, busy: true }), true)
  assert.equal(isActiveUpdate(null), false)
})
