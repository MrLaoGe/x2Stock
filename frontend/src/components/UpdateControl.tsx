import { useCallback, useEffect, useRef, useState } from 'react'
import { useI18n } from '../i18n'
import { updateMessages } from '../update-messages'
import { acceptUpdateStatus, installationRequest, isActiveUpdate } from '../update-state'
import type { UpdateCandidate, UpdateStatus } from '../update-contract'
import { Button } from './ui'

export function UpdateControl() {
  const { language } = useI18n()
  const t = updateMessages[language]
  const bridge = window.x2stockDesktop?.updates
  const dialog = useRef<HTMLDialogElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  const mounted = useRef(false)
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<UpdateStatus | null>(null)
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)
  const [confirmation, setConfirmation] = useState<UpdateCandidate | null>(null)
  const active = pending || isActiveUpdate(status)

  const accept = useCallback((next: UpdateStatus) => {
    if (!mounted.current) return
    setStatus((current) => acceptUpdateStatus(current, next))
    setFailed(false)
  }, [])

  useEffect(() => {
    mounted.current = true
    if (bridge) void bridge.getStatus().then(accept).catch(() => {
      if (mounted.current) setFailed(true)
    })
    return () => { mounted.current = false }
  }, [bridge, accept])

  // Poll only during active operations. Clean up on terminal status and unmount.
  useEffect(() => {
    if (!bridge || !active || failed) return
    let stopped = false
    let timer: ReturnType<typeof setTimeout>
    async function poll() {
      try {
        const next = await bridge!.getStatus()
        if (stopped) return
        accept(next)
        timer = setTimeout(() => { void poll() }, 750)
      } catch {
        if (!stopped) setFailed(true)
      }
    }
    timer = setTimeout(() => { void poll() }, 750)
    return () => { stopped = true; clearTimeout(timer) }
  }, [bridge, active, failed, accept])

  useEffect(() => {
    if (open && !dialog.current?.open) dialog.current?.showModal()
    if (!open && dialog.current?.open) dialog.current?.close()
  }, [open])

  async function check() {
    if (!bridge || (active && !failed)) return
    setPending(true)
    setFailed(false)
    setConfirmation(null)
    try { accept(await (failed ? bridge.getStatus() : bridge.check())) } catch { if (mounted.current) setFailed(true) }
    finally { if (mounted.current) setPending(false) }
  }

  async function install() {
    const request = installationRequest(status, confirmation)
    if (!bridge || !request || pending) return
    setPending(true)
    setConfirmation(null)
    setFailed(false)
    try { accept(await bridge.install(request)) } catch { if (mounted.current) setFailed(true) }
    finally { if (mounted.current) setPending(false) }
  }

  const candidate = confirmation ?? status?.candidate
  const number = new Intl.NumberFormat(language)
  const published = candidate && Number.isFinite(Date.parse(candidate.publishedAt))
    ? new Intl.DateTimeFormat(language, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(candidate.publishedAt)) : t.unknownVersion
  const phaseMessages = { idle: t.idle, checking: t.checking, available: t.available, 'no-update': t.noUpdate, downloading: t.downloading, verifying: t.verifying, staged: t.staged, applying: t.applying, error: t.error }

  function close() {
    setConfirmation(null)
    setOpen(false)
    trigger.current?.focus()
  }

  return <>
    <button ref={trigger} type="button" className="update-trigger" aria-haspopup="dialog" aria-controls="update-dialog" aria-expanded={open} onClick={() => setOpen(true)}>{t.updates}</button>
    <dialog id="update-dialog" ref={dialog} className="update-dialog" aria-labelledby="update-title" onCancel={(event) => { event.preventDefault(); close() }} onClose={() => { setConfirmation(null); setOpen(false); trigger.current?.focus() }}>
      <div className="update-header"><h2 id="update-title">{confirmation ? t.confirmTitle : t.updates}</h2><Button variant="secondary" onClick={close}>{t.close}</Button></div>
      {!bridge ? <p>{t.desktopOnly}</p> : <>
        <dl className="update-details"><div><dt>{t.current}</dt><dd>{status?.currentVersion ?? t.unknownVersion}</dd></div></dl>
        <p role="status" aria-live="polite">{failed ? t.checkFailed : status ? phaseMessages[status.phase] : t.unknownVersion}</p>
        {status?.phase === 'error' && <p role="alert">{status.errorCode ? t.errors[status.errorCode] ?? t.error : t.error}</p>}
        {candidate && <>
          <dl className="update-details">
            <div><dt>{t.candidate}</dt><dd>{candidate.version}</dd></div>
            <div><dt>{t.size}</dt><dd>{number.format(candidate.sizeBytes)} B</dd></div>
            <div><dt>{t.published}</dt><dd>{published}</dd></div>
          </dl>
          <h3>{t.notes}</h3><pre className="release-notes">{candidate.notes || t.noNotes}</pre>
        </>}
        {status?.downloadedBytes !== undefined && <p aria-live="polite">{number.format(status.downloadedBytes)} B{status.candidate ? ` / ${number.format(status.candidate.sizeBytes)} B` : ''}</p>}
        {confirmation ? <>
          <p>{t.confirmBody}</p>
          <div className="control-row"><Button disabled={!installationRequest(status, confirmation) || pending} onClick={() => { void install() }}>{t.confirmInstall}</Button><Button variant="secondary" onClick={() => setConfirmation(null)}>{t.cancel}</Button></div>
        </> : <div className="control-row">
          <Button disabled={active && !failed} onClick={() => { void check() }}>{failed ? t.refresh : t.check}</Button>
          {status?.phase === 'available' && status.candidate && <Button disabled={active} onClick={() => setConfirmation(status.candidate!)}>{t.install}</Button>}
        </div>}
      </>}
    </dialog>
  </>
}
