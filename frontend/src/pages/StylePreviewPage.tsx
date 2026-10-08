import { useState } from 'react'
import { Button, Notice, SelectInput, TextInput } from '../components/ui'

export function StylePreviewPage() {
  const [saved, setSaved] = useState(false)
  const [sampleText, setSampleText] = useState('')
  const [density, setDensity] = useState('舒适')

  function reset() {
    setSaved(false)
    setSampleText('')
    setDensity('舒适')
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">STYLE BASELINE / 01</p>
          <h1>界面规范预览</h1>
          <p>这是给后续页面使用的中性组件样例，不代表已经上线的业务设置或数据能力。交互状态可操作，也可以随时重置。</p>
        </div>
        <Button variant="secondary" onClick={reset}>重置示例</Button>
      </div>
      <div className="preview-grid">
        <section className="preview-card" aria-labelledby="actions-title">
          <h2 id="actions-title">动作与状态</h2>
          <p>按钮使用中性表面色，蓝色只用于可识别的交互文字与焦点。</p>
          <div className="control-row">
            <Button onClick={() => setSaved(true)}>{saved ? '已保存示例' : '保存示例'}</Button>
            <Button variant="secondary" onClick={() => setSaved(false)}>取消</Button>
          </div>
          <p className="code-note" aria-live="polite">状态：{saved ? '保存动作已触发（仅本地示例）' : '等待操作'}</p>
        </section>
        <section className="preview-card" aria-labelledby="fields-title">
          <h2 id="fields-title">输入与选择</h2>
          <p>表单保留明确的键盘焦点，弱化提示文字提高到可读的对比度。</p>
          <label className="field">
            <span className="field-label">示例名称</span>
            <TextInput value={sampleText} onChange={(event) => setSampleText(event.target.value)} placeholder="输入一段本地示例文字" />
          </label>
          <label className="field" style={{ display: 'block', marginTop: 14 }}>
            <span className="field-label">密度偏好</span>
            <SelectInput value={density} onChange={(event) => setDensity(event.target.value)}>
              <option>舒适</option><option>紧凑</option>
            </SelectInput>
          </label>
        </section>
        <section className="preview-card wide" aria-labelledby="notice-title">
          <h2 id="notice-title">信息提示</h2>
          <p>状态文字应说明发生了什么，不能只依赖颜色传递含义。</p>
          <Notice>这是一个界面状态示例。实际数据接入后，来源、时间和缺失原因会在对应模块中明确展示。</Notice>
        </section>
        <section className="preview-card wide" aria-labelledby="table-title">
          <h2 id="table-title">表格层级</h2>
          <p>表格允许在窄屏横向滚动，保留行列识别，不预填任何金融数据。</p>
          <div className="table-wrap">
            <table className="sample-table">
              <thead><tr><th>示例字段</th><th>状态</th><th>说明</th></tr></thead>
              <tbody>
                <tr><td>数据源</td><td>未配置</td><td>等待后续模块接入</td></tr>
                <tr><td>更新时间</td><td>—</td><td>当前没有可展示记录</td></tr>
                <tr><td>研究空间</td><td>本机</td><td>阶段 0 设计预览</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  )
}
