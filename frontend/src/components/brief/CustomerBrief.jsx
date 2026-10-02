import { Zap, AlertTriangle, Smartphone, ShieldCheck, ShieldAlert } from 'lucide-react'

export default function CustomerBrief({ customer, brief }) {
  const eligible = customer.upgrade_eligibility?.eligible
  const tradeIn = customer.upgrade_eligibility?.trade_in_value
  const openIssues = customer.open_issues || []
  const isPAH = customer.primary_holder?.is_present
  const initials = (customer.name || '')
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)

  return (
    <div className="card flex flex-col gap-4">

      {/* Identity */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 rounded-full bg-magenta/20 border border-magenta/40 flex items-center justify-center flex-shrink-0">
            <span className="text-magenta font-bold text-sm">{initials}</span>
          </div>
          <div className="min-w-0">
            <h2 className="text-white font-semibold text-base truncate">{customer.name}</h2>
            <p className="text-text-secondary text-xs">
              {customer.phone} · {customer.account_id}
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          {openIssues.length > 0 && (
            <span className="bg-status-error/15 text-status-error text-xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-status-error" />
              {openIssues.length} open
            </span>
          )}
          {/* Authorisation is the constraint that decides whether the rep can
              act at all, so it stays visible rather than living in a modal. */}
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${
              isPAH
                ? 'bg-status-success/15 text-status-success'
                : 'bg-status-warning/15 text-status-warning'
            }`}
          >
            {isPAH ? <ShieldCheck size={11} /> : <ShieldAlert size={11} />}
            {isPAH ? 'PAH present' : 'Non-PAH'}
          </span>
        </div>
      </div>

      {/* Plan + upgrade */}
      <div className="grid grid-cols-2 gap-3">
        <div className="card-dark !p-3">
          <p className="section-label mb-1.5">Current plan</p>
          <p className="text-white font-semibold text-sm">{customer.current_plan?.name}</p>
          <p className="text-magenta font-bold text-xl leading-tight">
            ${customer.current_plan?.monthly_total}
            <span className="text-text-secondary text-xs font-normal">/mo</span>
          </p>
          <p className="text-text-secondary text-xs mt-0.5">
            {customer.current_plan?.lines} line{customer.current_plan?.lines > 1 ? 's' : ''}
          </p>
        </div>

        <div className="card-dark !p-3">
          <p className="section-label mb-1.5">Upgrade</p>
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              eligible
                ? 'bg-status-success/15 text-status-success'
                : 'bg-brand-border text-text-secondary'
            }`}
          >
            {eligible ? 'Eligible' : 'Not yet'}
          </span>
          {tradeIn > 0 && (
            <p className="text-magenta font-bold text-xl leading-tight mt-1.5">
              ${tradeIn}
              <span className="text-text-secondary text-xs font-normal"> trade-in</span>
            </p>
          )}
          <p className="text-text-secondary text-xs mt-0.5 flex items-center gap-1">
            <Smartphone size={10} className="flex-shrink-0" />
            {customer.upgrade_eligibility?.current_device}
          </p>
        </div>
      </div>

      {/* AI brief */}
      {brief && !brief.parse_error && (
        <div className="border-t border-brand-border pt-3">
          <div className="flex items-center gap-2 mb-2">
            <Zap size={12} className="text-magenta" />
            <p className="section-label">AI brief</p>
          </div>

          <div className="flex flex-col gap-2">
            {[brief.plan_summary, brief.upgrade_status, brief.bill_summary]
              .filter(Boolean)
              .map((line, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-magenta flex-shrink-0 mt-1.5" />
                  <p className="text-text-muted text-sm leading-relaxed">{line}</p>
                </div>
              ))}
          </div>

          {brief.open_issues?.length > 0 && (
            <div className="mt-3 bg-status-error/5 border border-status-error/20 rounded-lg px-3 py-2.5">
              <div className="flex items-center gap-2 mb-1.5">
                <AlertTriangle size={12} className="text-status-error flex-shrink-0" />
                <p className="text-status-error text-xs font-semibold uppercase tracking-wide">
                  Resolve first
                </p>
              </div>
              {brief.open_issues.map((issue, i) => (
                <p key={i} className="text-text-muted text-xs leading-relaxed">{issue}</p>
              ))}
            </div>
          )}

          {brief.pah_status && (
            <p className="text-text-secondary text-xs mt-2.5">{brief.pah_status}</p>
          )}
        </div>
      )}
    </div>
  )
}
