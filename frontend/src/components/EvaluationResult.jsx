import { motion, useReducedMotion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, XCircle, Loader2 } from 'lucide-react'

export default function EvaluationResult({
  phase,
  rfpId,
  record,
  flaggedCriteria,
  errorMessage,
  elapsedLabel,
  onReset,
}) {
  const reduceMotion = useReducedMotion()
  const fadeIn = {
    initial: reduceMotion ? undefined : { opacity: 0, y: 8 },
    animate: reduceMotion ? undefined : { opacity: 1, y: 0 },
    transition: { duration: 0.3, ease: 'easeOut' },
  }

  if (phase === 'uploading' || phase === 'evaluating') {
    return (
      <motion.div {...fadeIn} className="rounded-card border border-line bg-elevated px-6 py-12 text-center">
        <Loader2 size={24} className="mx-auto animate-spin text-accent" />
        <p className="mt-4 text-sm text-subtle">
          {phase === 'uploading'
            ? 'Uploading...'
            : 'Evaluating against government procurement norms. This can take a while on CPU-only hardware.'}
        </p>
        {phase === 'evaluating' && (
          <p className="mt-1 text-xs text-subtle">
            Typically 15-25 minutes for a full RFP (roughly 20-40 seconds per criterion).
            {elapsedLabel && <> Elapsed: {elapsedLabel}.</>}
          </p>
        )}
        {rfpId && <p className="mt-1 text-xs text-subtle/70">RFP ID: {rfpId}</p>}
        <div className="mx-auto mt-6 max-w-xs space-y-2">
          <div className="h-2 animate-pulse rounded-full bg-surface" />
          <div className="h-2 w-4/5 animate-pulse rounded-full bg-surface" />
          <div className="h-2 w-3/5 animate-pulse rounded-full bg-surface" />
        </div>
      </motion.div>
    )
  }

  if (phase === 'success') {
    return (
      <motion.div
        {...fadeIn}
        className="rounded-card border border-success-line bg-success-soft px-6 py-8"
      >
        <div className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-success" />
          <h2 className="text-sm font-semibold text-success">RFP published successfully and stored.</h2>
        </div>
        <dl className="mt-4 space-y-1 text-sm text-ink">
          <div className="flex gap-2">
            <dt className="font-medium text-subtle">RFP ID:</dt>
            <dd>{record?.rfpId}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="font-medium text-subtle">Criteria evaluated:</dt>
            <dd>{record?.criteriaCount}</dd>
          </div>
        </dl>
        <button
          onClick={onReset}
          className="mt-6 text-sm font-medium text-success underline decoration-success/40 underline-offset-2 transition-colors hover:decoration-success"
        >
          Upload another RFP
        </button>
      </motion.div>
    )
  }

  if (phase === 'invalid') {
    return (
      <motion.div {...fadeIn} className="rounded-card border border-danger-line bg-danger-soft px-6 py-8">
        <div className="flex items-center gap-2">
          <AlertTriangle size={18} className="text-danger" />
          <h2 className="text-sm font-semibold text-danger">
            This RFP has {flaggedCriteria.length} criteria that need attention.
          </h2>
        </div>
        <ul className="mt-4 space-y-3">
          {flaggedCriteria.map((c) => (
            <li key={c.id} className="rounded-md border border-danger-line bg-elevated px-4 py-3">
              <p className="text-sm font-medium text-ink">{c.text}</p>
              <p className="mt-1 text-sm text-danger">{c.compliance_issue}</p>
              {c.compliance_citation && (
                <p className="mt-1 text-xs text-subtle">
                  Citation: {c.compliance_citation.norm_name}
                  {c.compliance_citation.clause_ref ? `, clause ${c.compliance_citation.clause_ref}` : ''}
                  {c.compliance_citation.page_number ? `, page ${c.compliance_citation.page_number}` : ''}
                </p>
              )}
            </li>
          ))}
        </ul>
        <button
          onClick={onReset}
          className="mt-6 text-sm font-medium text-danger underline decoration-danger/40 underline-offset-2 transition-colors hover:decoration-danger"
        >
          Upload a revised RFP
        </button>
      </motion.div>
    )
  }

  return (
    <motion.div {...fadeIn} className="rounded-card border border-danger-line bg-danger-soft px-6 py-8">
      <div className="flex items-center gap-2">
        <XCircle size={18} className="text-danger" />
        <h2 className="text-sm font-semibold text-danger">Something went wrong.</h2>
      </div>
      <p className="mt-1 text-sm text-danger">{errorMessage}</p>
      <button
        onClick={onReset}
        className="mt-6 text-sm font-medium text-danger underline decoration-danger/40 underline-offset-2 transition-colors hover:decoration-danger"
      >
        Try again
      </button>
    </motion.div>
  )
}
