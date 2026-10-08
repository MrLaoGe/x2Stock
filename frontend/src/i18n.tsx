import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type Language = 'zh-CN' | 'zh-TW' | 'en'
type Messages = {
  metaDescription: string
  home: string; preview: string; localSpace: string; notConnected: string; stageNote: string
  eyebrowHome: string; homeTitle: string; homeLede: string; workspaceEmpty: string; emptyDescription: string
  emptyStatus: string; browsePreview: string; language: string; languageName: string
  eyebrowPreview: string; previewTitle: string; previewDescription: string; reset: string
  actionsTitle: string; actionsDescription: string; save: string; saved: string; cancel: string
  stateSaved: string; stateWaiting: string; stateLabel: string; fieldsTitle: string; fieldsDescription: string
  sampleName: string; samplePlaceholder: string; density: string; comfortable: string; compact: string
  noticeTitle: string; noticeDescription: string; noticeText: string; tableTitle: string
  tableDescription: string; field: string; status: string; explanation: string; source: string
  unconfigured: string; waitingForModule: string; updateTime: string; noRecords: string
  researchSpace: string; local: string; previewStage: string; notFoundTitle: string; notFoundDescription: string
}

const messages: Record<Language, Messages> = {
  'zh-CN': {
    metaDescription: 'XXStock 本机研究工作台',
    home: '工作台', preview: '规范预览', localSpace: '本机空间', notConnected: '未连接数据服务', stageNote: '本机研究空间 · 阶段 0 · 风格基线',
    eyebrowHome: 'XXSTOCK / LOCAL WORKSPACE', homeTitle: '为值得验证的判断，留出一张干净的桌面。',
    homeLede: '这里是 XXStock 的本机研究工作台。它现在保持空白，等待后续模块逐一接入；没有数据时，也不替你制造结论。',
    workspaceEmpty: '工作台尚未配置', emptyDescription: '当前版本只确定界面基线，数据服务和研究模块尚未启用。你可以先浏览组件规范，了解之后页面会遵循的视觉与交互约定。',
    emptyStatus: '空状态 · 设计阶段', browsePreview: '浏览规范预览', language: '界面语言', languageName: '简体中文',
    eyebrowPreview: 'STYLE BASELINE / 01', previewTitle: '界面规范预览', previewDescription: '这是给后续页面使用的中性组件样例，不代表已经上线的业务设置或数据能力。交互状态可操作，也可以随时重置。', reset: '重置示例',
    actionsTitle: '动作与状态', actionsDescription: '按钮使用中性表面色，蓝色只用于可识别的交互文字与焦点。', save: '保存示例', saved: '已保存示例', cancel: '取消',
    stateSaved: '保存动作已触发（仅本地示例）', stateWaiting: '等待操作', stateLabel: '状态', fieldsTitle: '输入与选择', fieldsDescription: '表单保留明确的键盘焦点，弱化提示文字提高到可读的对比度。',
    sampleName: '示例名称', samplePlaceholder: '输入一段本地示例文字', density: '密度偏好', comfortable: '舒适', compact: '紧凑',
    noticeTitle: '信息提示', noticeDescription: '状态文字应说明发生了什么，不能只依赖颜色传递含义。', noticeText: '这是一个界面状态示例。实际数据接入后，来源、时间和缺失原因会在对应模块中明确展示。',
    tableTitle: '表格层级', tableDescription: '表格允许在窄屏横向滚动，保留行列识别，不预填任何金融数据。', field: '示例字段', status: '状态', explanation: '说明', source: '数据源', unconfigured: '未配置', waitingForModule: '等待后续模块接入', updateTime: '更新时间', noRecords: '当前没有可展示记录', researchSpace: '研究空间', local: '本机', previewStage: '阶段 0 设计预览', notFoundTitle: '找不到这个页面', notFoundDescription: '当前地址没有对应的页面。请返回工作台。',
  },
  'zh-TW': {
    metaDescription: 'XXStock 本機研究工作台',
    home: '工作台', preview: '規範預覽', localSpace: '本機空間', notConnected: '未連接資料服務', stageNote: '本機研究空間 · 階段 0 · 風格基線',
    eyebrowHome: 'XXSTOCK / LOCAL WORKSPACE', homeTitle: '為值得驗證的判斷，留一張乾淨的桌面。',
    homeLede: '這裡是 XXStock 的本機研究工作台。目前保持空白，等待後續模組逐一接入；沒有資料時，也不替你製造結論。',
    workspaceEmpty: '工作台尚未設定', emptyDescription: '目前版本只確立介面基線，資料服務和研究模組尚未啟用。你可以先瀏覽元件規範，了解後續頁面會遵循的視覺與互動約定。',
    emptyStatus: '空狀態 · 設計階段', browsePreview: '瀏覽規範預覽', language: '介面語言', languageName: '繁體中文',
    eyebrowPreview: 'STYLE BASELINE / 01', previewTitle: '介面規範預覽', previewDescription: '這是供後續頁面使用的中性元件範例，不代表已上線的業務設定或資料能力。互動狀態可操作，也可以隨時重設。', reset: '重設範例',
    actionsTitle: '動作與狀態', actionsDescription: '按鈕使用中性表面色，藍色只用於可辨識的互動文字與焦點。', save: '儲存範例', saved: '已儲存範例', cancel: '取消',
    stateSaved: '已觸發儲存動作（僅本機範例）', stateWaiting: '等待操作', stateLabel: '狀態', fieldsTitle: '輸入與選擇', fieldsDescription: '表單保留明確的鍵盤焦點，並提高提示文字的對比度。',
    sampleName: '範例名稱', samplePlaceholder: '輸入一段本機範例文字', density: '密度偏好', comfortable: '舒適', compact: '緊湊',
    noticeTitle: '資訊提示', noticeDescription: '狀態文字應說明發生了什麼，不能只依賴顏色傳達含義。', noticeText: '這是介面狀態範例。接入實際資料後，來源、時間和缺失原因會在對應模組中明確顯示。',
    tableTitle: '表格層級', tableDescription: '表格可在窄螢幕橫向捲動，保留列欄辨識，不預填任何金融資料。', field: '範例欄位', status: '狀態', explanation: '說明', source: '資料來源', unconfigured: '未設定', waitingForModule: '等待後續模組接入', updateTime: '更新時間', noRecords: '目前沒有可顯示的記錄', researchSpace: '研究空間', local: '本機', previewStage: '階段 0 設計預覽', notFoundTitle: '找不到這個頁面', notFoundDescription: '目前網址沒有對應頁面。請返回工作台。',
  },
  en: {
    metaDescription: 'Local XXStock research workspace',
    home: 'Workspace', preview: 'Style guide', localSpace: 'Local workspace', notConnected: 'Data service not connected', stageNote: 'Local research space · Stage 0 · Style baseline',
    eyebrowHome: 'XXSTOCK / LOCAL WORKSPACE', homeTitle: 'A clear desk for ideas worth testing.',
    homeLede: 'This is the local XXStock research workspace. It is intentionally empty while future modules are being planned. It will not invent conclusions when no data is available.',
    workspaceEmpty: 'Workspace not configured', emptyDescription: 'This release establishes the visual baseline only. Data services and research modules are not enabled. Preview the neutral components to see the visual and interaction conventions for future pages.',
    emptyStatus: 'Empty state · Design phase', browsePreview: 'View style guide', language: 'Language', languageName: 'English',
    eyebrowPreview: 'STYLE BASELINE / 01', previewTitle: 'Interface style guide', previewDescription: 'These neutral components are examples for future pages. They do not represent live settings or data features. Interactions work locally and can be reset.', reset: 'Reset examples',
    actionsTitle: 'Actions and status', actionsDescription: 'Buttons use neutral surfaces. Blue is reserved for readable interactive text and focus.', save: 'Save example', saved: 'Example saved', cancel: 'Cancel',
    stateSaved: 'Save action triggered (local example only)', stateWaiting: 'Waiting for action', stateLabel: 'Status', fieldsTitle: 'Text and selection', fieldsDescription: 'Form controls keep a visible keyboard focus and readable placeholder contrast.',
    sampleName: 'Example name', samplePlaceholder: 'Type some local sample text', density: 'Density', comfortable: 'Comfortable', compact: 'Compact',
    noticeTitle: 'Information notice', noticeDescription: 'Status text explains what happened; color is never the only signal.', noticeText: 'This is an interface state example. When real data is connected, its source, time, and missing-data reason will be shown in the relevant module.',
    tableTitle: 'Table hierarchy', tableDescription: 'The table scrolls within its own container on narrow screens. No financial data is fabricated.', field: 'Example field', status: 'Status', explanation: 'Details', source: 'Data source', unconfigured: 'Not configured', waitingForModule: 'Waiting for a future module', updateTime: 'Updated', noRecords: 'No records to display', researchSpace: 'Research space', local: 'Local', previewStage: 'Stage 0 design preview', notFoundTitle: 'Page not found', notFoundDescription: 'There is no page at this address. Return to the workspace.',
  },
}

const languageOptions: { value: Language; label: string }[] = [
  { value: 'zh-CN', label: '简体中文' }, { value: 'zh-TW', label: '繁體中文' }, { value: 'en', label: 'English' },
]
const storageKey = 'xxstock.language'
const LanguageContext = createContext<{ language: Language; setLanguage: (value: Language) => void; t: Messages; languageOptions: typeof languageOptions } | null>(null)

function getSavedLanguage(): Language {
  try {
    const stored = localStorage.getItem(storageKey)
    return languageOptions.some((option) => option.value === stored) ? stored as Language : 'zh-CN'
  } catch {
    return 'zh-CN'
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(getSavedLanguage)
  const value = useMemo(() => ({
    language,
    setLanguage: setLanguageState,
    t: new Proxy(messages[language], {
      get(target, property, receiver) {
        if (typeof property === 'string' && !(property in target)) {
          if (import.meta.env.DEV) console.warn(`[i18n] Missing translation: ${language}.${property}`)
          return `⟦${property}⟧`
        }
        return Reflect.get(target, property, receiver)
      },
    }),
    languageOptions,
  }), [language])

  useEffect(() => {
    document.documentElement.lang = language
    document.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute('content', messages[language].metaDescription)
    try { localStorage.setItem(storageKey, language) } catch { /* Storage may be disabled in private contexts. */ }
  }, [language])

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useI18n() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useI18n must be used within LanguageProvider')
  return context
}
