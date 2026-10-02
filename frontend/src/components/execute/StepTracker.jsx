import { Check, X, RotateCw, Loader2 } from 'lucide-react'

// Status names come straight off the websocket messages in
// services/execution_service.py — pending / active / complete / error / retrying.
const STATUS_CONFIG = {
  pending: {
    dot: 'bg-brand-border-light',
    text: 'text-text-secondary',
  },
  active: {
    dot: 'bg-magenta',
    text: 'text-white',
    Icon: Loader2,
    iconClass: 'text-magenta animate-spin',
  },
  complete: {
    dot: 'bg-status-success',
    text: 'text-text-secondary',
    Icon: Check,
    iconClass: 'text-status-success',
  },
  error: {
    dot: 'bg-status-error',
    text: 'text-white',
    Icon: X,
    iconClass: 'text-status-error',
  },
  // The promo timeout is deliberate and recovers on its own — showing it as a
  // retry rather than a failure is the honest read, and it demonstrates the
  // agent handling a flaky downstream without a human stepping in.
  retrying: {
    dot: 'bg-status-warning',
    text: 'text-white',
    Icon: RotateCw,
    iconClass: 'text-status-warning animate-spin',
  },
}

export default function StepTracker({ steps }) {
  return (
    <div className="flex flex-col gap-0.5">
      {steps.map((step, i) => {
        const cfg = STATUS_CONFIG[step.status] || STATUS_CONFIG.pending
        const isLast = i === steps.length - 1

        return (
          <div key={step.id} className="flex gap-3">
            {/* Rail — connects the steps so they read as one sequence. */}
            <div className="flex flex-col items-center flex-shrink-0 pt-1">
              <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${cfg.dot}`} />
              {!isLast && <div className="w-px flex-1 bg-brand-border mt-1" />}
            </div>

            <div className={`flex-1 ${isLast ? 'pb-0' : 'pb-3'}`}>
              <div className="flex items-center gap-2">
                {cfg.Icon && <cfg.Icon size={12} className={`flex-shrink-0 ${cfg.iconClass}`} />}
                <p className={`text-sm leading-tight ${cfg.text} ${
                  step.status === 'complete' ? 'line-through decoration-brand-border-light' : ''
                }`}>
                  {step.name}
                </p>
              </div>

              {step.message && (
                <p className={`text-xs mt-0.5 ${
                  step.status === 'error' ? 'text-status-error' : 'text-status-warning'
                }`}>
                  {step.message}
                </p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
