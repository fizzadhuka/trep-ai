import { ShieldAlert, Check, X } from 'lucide-react'

export default function PAHPanel({ pahStatus }) {
  return (
    <div className="rounded-xl border border-status-warning/30 bg-status-warning/5 p-4">
      <div className="flex items-center gap-2 mb-1.5">
        <ShieldAlert size={14} className="text-status-warning flex-shrink-0" />
        <h2 className="text-status-warning font-semibold text-sm">PAH not present</h2>
      </div>

      <p className="text-text-muted text-xs leading-relaxed mb-3">
        Primary account holder{' '}
        <strong className="text-white font-semibold">{pahStatus.pah_name}</strong>{' '}
        is not in store. Some actions are restricted.
      </p>

      {/* Permitted first — a rep needs to know what they can still do for the
          person standing in front of them, not just what is blocked. */}
      <div className="flex flex-col gap-3 mb-3">
        {pahStatus.permitted_actions?.length > 0 && (
          <div>
            <p className="section-label mb-1.5">Can do now</p>
            <div className="flex flex-col gap-1">
              {pahStatus.permitted_actions.map((a, i) => (
                <p key={i} className="text-text-muted text-xs flex items-start gap-1.5">
                  <Check size={11} className="text-status-success flex-shrink-0 mt-0.5" />
                  {a}
                </p>
              ))}
            </div>
          </div>
        )}

        {pahStatus.restricted_actions?.length > 0 && (
          <div>
            <p className="section-label mb-1.5">Restricted</p>
            <div className="flex flex-col gap-1">
              {pahStatus.restricted_actions.map((a, i) => (
                <p key={i} className="text-text-secondary text-xs flex items-start gap-1.5">
                  <X size={11} className="flex-shrink-0 mt-0.5" />
                  <span className="line-through">{a}</span>
                </p>
              ))}
            </div>
          </div>
        )}
      </div>

      {pahStatus.explanation && (
        <p className="text-text-secondary text-xs leading-relaxed mb-3 border-t border-status-warning/20 pt-2.5">
          {pahStatus.explanation}
        </p>
      )}

      {pahStatus.authorization_options?.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="section-label">How to authorize</p>
          {pahStatus.authorization_options.map((opt, i) => (
            <button
              key={i}
              className="w-full bg-brand-card border border-brand-border hover:border-magenta text-white text-xs font-semibold py-2 rounded-lg transition-colors text-left px-3"
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
