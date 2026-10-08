import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readLanguagePreference, languageStorageKey } from '../src/language-preferences.ts'

const storage = (entries) => ({ getItem: (key) => entries[key] ?? null })
test('first run defaults to Simplified Chinese', () => {
  assert.equal(readLanguagePreference(storage({})), 'zh-CN')
})
test('valid legacy languages survive rename when the new preference is absent', () => {
  for (const language of ['zh-CN', 'zh-TW', 'en']) {
    assert.equal(readLanguagePreference(storage({ 'xxstock.language': language })), language)
  }
})
test('new preferences take priority over the legacy setting', () => {
  assert.equal(languageStorageKey, 'x2stock.language')
  assert.equal(readLanguagePreference(storage({ 'x2stock.language': 'zh-TW', 'xxstock.language': 'en' })), 'zh-TW')
})
test('invalid new preference uses the controlled default without reviving a legacy preference', () => {
  assert.equal(readLanguagePreference(storage({ 'x2stock.language': 'invalid', 'xxstock.language': 'en' })), 'zh-CN')
})
test('unavailable storage does not block the interface', () => {
  assert.equal(readLanguagePreference({ getItem() { throw new Error('Storage unavailable') } }), 'zh-CN')
})
