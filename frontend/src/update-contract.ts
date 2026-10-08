// Mirrors desktop/update-contract.d.ts. Keep the accepted IPC shape in sync.
export type UpdatePhase = 'idle' | 'checking' | 'available' | 'no-update' |
  'downloading' | 'verifying' | 'staged' | 'applying' | 'error'
export type UpdateError = 'busy' | 'network' | 'invalid-release' | 'no-assets' |
  'download' | 'hash' | 'archive' | 'bundle' | 'unsupported' | 'permissions' |
  'apply' | 'health' | 'rollback' | 'ipc'
export interface UpdateCandidate {
  releaseId: number
  version: string
  notes: string
  publishedAt: string
  sizeBytes: number
}
export interface UpdateStatus {
  revision: number
  phase: UpdatePhase
  currentVersion: string
  busy: boolean
  candidate?: UpdateCandidate
  downloadedBytes?: number
  errorCode?: UpdateError
}
export interface UpdateBridge {
  onStatus(listener: (status: UpdateStatus) => void): () => void
  getStatus(): Promise<UpdateStatus>
  check(): Promise<UpdateStatus>
  install(request: { releaseId: number; version: string; confirmed: true }): Promise<UpdateStatus>
}
declare global {
  interface Window {
    x2stockDesktop?: { updates?: UpdateBridge }
  }
}
