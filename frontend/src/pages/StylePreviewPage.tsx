import { useState } from 'react'
import { Button, Notice, SelectInput, TextInput } from '../components/ui'
import { useI18n } from '../i18n'

export function StylePreviewPage() {
  const { t } = useI18n()
  const [saved, setSaved] = useState(false)
  const [sampleText, setSampleText] = useState('')
  const [density, setDensity] = useState<'comfortable' | 'compact'>('comfortable')

  function reset() {
    setSaved(false)
    setSampleText('')
    setDensity('comfortable')
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">{t.eyebrowPreview}</p>
          <h1>{t.previewTitle}</h1>
          <p>{t.previewDescription}</p>
        </div>
        <Button variant="secondary" onClick={reset}>{t.reset}</Button>
      </div>
      <div className="preview-grid">
        <section className="preview-card" aria-labelledby="actions-title">
          <h2 id="actions-title">{t.actionsTitle}</h2>
          <p>{t.actionsDescription}</p>
          <div className="control-row">
            <Button onClick={() => setSaved(true)}>{saved ? t.saved : t.save}</Button>
            <Button variant="secondary" onClick={() => setSaved(false)}>{t.cancel}</Button>
          </div>
          <p className="code-note" aria-live="polite">{t.stateLabel}: {saved ? t.stateSaved : t.stateWaiting}</p>
        </section>
        <section className="preview-card" aria-labelledby="fields-title">
          <h2 id="fields-title">{t.fieldsTitle}</h2>
          <p>{t.fieldsDescription}</p>
          <label className="field">
            <span className="field-label">{t.sampleName}</span>
            <TextInput aria-label={t.sampleName} value={sampleText} onChange={(event) => setSampleText(event.target.value)} placeholder={t.samplePlaceholder} />
          </label>
          <label className="field" style={{ display: 'block', marginTop: 14 }}>
            <span className="field-label">{t.density}</span>
            <SelectInput aria-label={t.density} value={density} onChange={(event) => setDensity(event.target.value as typeof density)}>
              <option value="comfortable">{t.comfortable}</option><option value="compact">{t.compact}</option>
            </SelectInput>
          </label>
        </section>
        <section className="preview-card wide" aria-labelledby="notice-title">
          <h2 id="notice-title">{t.noticeTitle}</h2>
          <p>{t.noticeDescription}</p>
          <Notice>{t.noticeText}</Notice>
        </section>
        <section className="preview-card wide" aria-labelledby="table-title">
          <h2 id="table-title">{t.tableTitle}</h2>
          <p>{t.tableDescription}</p>
          <div className="table-wrap">
            <table className="sample-table">
              <thead><tr><th>{t.field}</th><th>{t.status}</th><th>{t.explanation}</th></tr></thead>
              <tbody>
                <tr><td>{t.source}</td><td>{t.unconfigured}</td><td>{t.waitingForModule}</td></tr>
                <tr><td>{t.updateTime}</td><td>—</td><td>{t.noRecords}</td></tr>
                <tr><td>{t.researchSpace}</td><td>{t.local}</td><td>{t.previewStage}</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
