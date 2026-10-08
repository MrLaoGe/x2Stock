import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { StylePreviewPage } from './pages/StylePreviewPage'
import { WorkspacePage } from './pages/WorkspacePage'
import './styles/app.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HashRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<WorkspacePage />} />
          <Route path="style-preview" element={<StylePreviewPage />} />
        </Route>
      </Routes>
    </HashRouter>
  </StrictMode>,
)
