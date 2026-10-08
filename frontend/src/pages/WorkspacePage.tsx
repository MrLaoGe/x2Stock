import { Link } from 'react-router-dom'

export function WorkspacePage() {
  return (
    <div className="page workspace-page">
      <p className="eyebrow">XXSTOCK / LOCAL WORKSPACE</p>
      <h1>为值得验证的判断，留出一张干净的桌面。</h1>
      <p className="lede">这里是 XXStock 的本机研究工作台。它现在保持空白，等待后续模块逐一接入；没有数据时，也不替你制造结论。</p>
      <section className="empty-state" aria-labelledby="empty-title">
        <div className="empty-copy">
          <h2 id="empty-title">工作台尚未配置</h2>
          <p>当前版本只确定界面基线，数据服务和研究模块尚未启用。你可以先浏览组件规范，了解之后页面会遵循的视觉与交互约定。</p>
          <Link className="button secondary" to="/style-preview" style={{ display: 'inline-flex', alignItems: 'center', marginTop: 20 }}>浏览规范预览</Link>
        </div>
        <span className="status-chip">空状态 · 设计阶段</span>
      </section>
    </div>
  )
}
