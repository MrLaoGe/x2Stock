export type Language = 'zh-CN' | 'zh-TW' | 'en'
export const languageStorageKey = 'x2stock.language'
const legacyStorageKey = 'xxstock.language'

/** New preferences win; legacy preferences are read only when the new key is absent. */
export function readLanguagePreference(storage: Pick<Storage, 'getItem'>): Language {
  try {
    const current = storage.getItem(languageStorageKey)
    const value = current === null ? storage.getItem(legacyStorageKey) : current
    return value === 'zh-CN' || value === 'zh-TW' || value === 'en' ? value : 'zh-CN'
  } catch {
    return 'zh-CN'
  }
}
