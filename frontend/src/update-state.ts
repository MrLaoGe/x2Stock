import type { UpdateCandidate, UpdateStatus } from './update-contract.ts'

export function isActiveUpdate(status: UpdateStatus | null): boolean {
  return !!status && (status.busy || ['checking', 'downloading', 'verifying', 'staged', 'applying'].includes(status.phase))
}

export function acceptUpdateStatus(current: UpdateStatus | null, incoming: UpdateStatus): UpdateStatus {
  return current && incoming.revision < current.revision ? current : incoming
}

/** The confirmation is tied to a specific checked release; a changed candidate needs new consent. */
export function installationRequest(status: UpdateStatus | null, confirmed: UpdateCandidate | null) {
  if (!status || status.phase !== 'available' || status.busy || !status.candidate || !confirmed ||
    status.candidate.releaseId !== confirmed.releaseId || status.candidate.version !== confirmed.version) return null
  return { releaseId: confirmed.releaseId, version: confirmed.version, confirmed: true as const }
}
