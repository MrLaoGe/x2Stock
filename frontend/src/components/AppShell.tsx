import { useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useI18n } from '../i18n'
import { UpdateControl } from './UpdateControl'

export function AppShell() {
  const { t, language, setLanguage, languageOptions } = useI18n()
  const location = useLocation()
  useEffect(() => {
    const pageTitle = location.pathname === '/style-preview' ? t.previewTitle : location.pathname === '/' ? t.home : t.notFoundTitle
    document.title = `x2Stock | ${pageTitle}`
  }, [location.pathname, t.home, t.previewTitle])
  const navigation = [
    { to: '/', label: t.home, icon: '○', end: true },
    { to: '/style-preview', label: t.preview, icon: '◇', end: false },
  ]

  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label={t.navigation}>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">X</span>
          <span className="brand-name">x2Stock</span>
        </div>
        <nav>
          <ul className="nav-list">
            {navigation.map((item) => (
              <li key={item.to}>
                <NavLink className="nav-link" to={item.to} end={item.end}>
                  <span className="nav-icon" aria-hidden="true">{item.icon}</span>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <p className="sidebar-foot">{t.stageNote}</p>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <span className="topbar-context">{t.localSpace} · {t.notConnected}</span>
          <div className="topbar-actions">
            <UpdateControl />
            <label className="sr-only" htmlFor="language-select">{t.language}</label>
            <select id="language-select" className="language-select" value={language} onChange={(event) => setLanguage(event.target.value as typeof language)}>
              {languageOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
            <NavLink className="topbar-link" to="/style-preview">{t.preview}</NavLink>
          </div>
        </header>
        <main><Outlet /></main>
      </div>
    </div>
  )
}
