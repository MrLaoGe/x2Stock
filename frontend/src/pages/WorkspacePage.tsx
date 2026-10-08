import { Link } from 'react-router-dom'
import { useI18n } from '../i18n'

export function WorkspacePage() {
  const { t } = useI18n()
  return (
    <div className="page workspace-page">
      <p className="eyebrow">{t.eyebrowHome}</p>
      <h1>{t.homeTitle}</h1>
      <p className="lede">{t.homeLede}</p>
      <section className="empty-state" aria-labelledby="empty-title">
        <div className="empty-copy">
          <h2 id="empty-title">{t.workspaceEmpty}</h2>
          <p>{t.emptyDescription}</p>
          <Link className="button secondary" to="/style-preview" style={{ display: 'inline-flex', alignItems: 'center', marginTop: 20 }}>{t.browsePreview}</Link>
        </div>
        <span className="status-chip">{t.emptyStatus}</span>
      </section>
    </div>
  )
}
