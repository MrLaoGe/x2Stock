import { Link } from 'react-router-dom'
import { useI18n } from '../i18n'

export function NotFoundPage() {
  const { t } = useI18n()
  return <div className="page"><p className="eyebrow">XXSTOCK</p><h1>{t.notFoundTitle}</h1><p className="lede">{t.notFoundDescription}</p><Link className="button secondary" to="/" style={{ display: 'inline-flex', alignItems: 'center', marginTop: 24 }}>{t.home}</Link></div>
}
