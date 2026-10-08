import { NavLink, Outlet } from 'react-router-dom'

const navigation = [
  { to: '/', label: '工作台', icon: '○', end: true },
  { to: '/style-preview', label: '规范预览', icon: '◇', end: false },
]

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label="主导航">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">X</span>
          <span className="brand-name">XXStock</span>
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
        <p className="sidebar-foot">本机研究空间<br />阶段 0 · 风格基线</p>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <span className="topbar-context">本机空间 · 未连接数据服务</span>
          <NavLink className="topbar-link" to="/style-preview">查看界面规范</NavLink>
        </header>
        <main><Outlet /></main>
      </div>
    </div>
  )
}
