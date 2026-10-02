import { useState } from 'react'
import { CheckCircle2, Mail, RefreshCw } from 'lucide-react'

function formatDate() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
}

const TRANSACTION_LABELS = {
  trade_in_upgrade:  'Trade-in and plan upgrade',
  plan_upgrade_only: 'Plan upgrade',
}

export default function CommitmentSnapshot({ customer, brief, transaction, finalBill, onNewVisit }) {
  const [emailSent, setEmailSent] = useState(false)

  const transactionLabel =
    TRANSACTION_LABELS[transaction?.transaction_type] ||
    transaction?.transaction_type?.replace(/_/g, ' ') ||
    'Account update'

  const previousTotal = customer.current_plan?.monthly_total
  const newTotal = finalBill?.new_monthly_total
  const delta = newTotal != null && previousTotal != null ? newTotal - previousTotal : null
  const firstName = customer.name?.split(' ')[0] || 'there'
  const newPlanName = transaction?.params?.proposed_plan || customer.current_plan?.name

  return (
    <div className="animate-fade-in">

      {/* Hero — this screen is handed to the customer, so it leads with a plain
          statement of what happened rather than internal transaction language. */}
      <div className="bg-magenta-gradient px-8 py-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-2 text-white/70 text-sm mb-3">
            <CheckCircle2 size={14} />
            <span>Visit complete · {formatDate()}</span>
          </div>
          <h1 className="text-white text-3xl font-bold tracking-tight mb-1">Commitment Snapshot</h1>
          <div className="w-10 h-0.5 bg-white/40 rounded-full mb-3" />
          <p className="text-white/80 text-sm">
            Everything discussed and completed today — {firstName}, keep this for your records.
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-8 grid grid-cols-2 gap-6 items-start">

        {/* LEFT — what happened */}
        <div className="flex flex-col gap-4">

          {brief && !brief.parse_error && (
            <div className="card">
              <p className="section-label mb-3">Your visit</p>
              <div className="flex flex-col gap-2">
                {[brief.plan_summary, brief.upgrade_status].filter(Boolean).map((line, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-magenta flex-shrink-0 mt-2" />
                    <p className="text-text-muted text-sm leading-relaxed">{line}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {transaction && (
            <div className="card">
              <p className="section-label mb-3">Changes made</p>
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-3 rounded-lg border border-magenta/20 bg-magenta/5 px-3 py-2.5">
                  <CheckCircle2 size={14} className="text-magenta flex-shrink-0" />
                  <div>
                    <p className="text-magenta text-sm font-semibold">{transactionLabel}</p>
                    {transaction.params?.proposed_plan && (
                      <p className="text-text-secondary text-xs">
                        {customer.current_plan?.name} → {transaction.params.proposed_plan}
                      </p>
                    )}
                  </div>
                </div>

                {finalBill?.promo_applied && (
                  <div className="flex items-center gap-3 rounded-lg border border-status-success/20 bg-status-success/5 px-3 py-2.5">
                    <CheckCircle2 size={14} className="text-status-success flex-shrink-0" />
                    <div>
                      <p className="text-status-success text-sm font-semibold">Promotion applied</p>
                      <p className="text-text-secondary text-xs">{finalBill.promo_applied}</p>
                    </div>
                  </div>
                )}

                {finalBill?.one_time_credit > 0 && (
                  <div className="flex items-center gap-3 rounded-lg border border-status-success/20 bg-status-success/5 px-3 py-2.5">
                    <CheckCircle2 size={14} className="text-status-success flex-shrink-0" />
                    <div>
                      <p className="text-status-success text-sm font-semibold">
                        ${Number(finalBill.one_time_credit).toFixed(2)} credit
                      </p>
                      <p className="text-text-secondary text-xs">Applied to your account</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — the money and what happens next */}
        <div className="flex flex-col gap-4">

          {finalBill && (
            <div className={`rounded-xl border p-5 ${
              delta != null && delta < 0
                ? 'bg-status-success/5 border-status-success/30'
                : 'bg-magenta/5 border-magenta/30'
            }`}>
              <p className="section-label mb-2">New monthly bill</p>

              <div className="flex items-end justify-between mb-3">
                <p className="text-white text-4xl font-bold leading-none">
                  ${Number(newTotal).toFixed(0)}
                  <span className="text-text-secondary text-base font-normal">/mo</span>
                </p>
                <div className="text-right">
                  {previousTotal != null && delta !== 0 && (
                    <p className="text-text-secondary text-xs line-through">
                      ${Number(previousTotal).toFixed(0)}/mo before
                    </p>
                  )}
                  {delta != null && delta !== 0 && (
                    <p className={`text-sm font-semibold mt-0.5 ${
                      delta < 0 ? 'text-status-success' : 'text-magenta'
                    }`}>
                      {delta < 0
                        ? `Save $${Math.abs(delta).toFixed(0)}/mo`
                        : `+$${delta.toFixed(0)}/mo`}
                    </p>
                  )}
                </div>
              </div>

              {finalBill.breakdown?.length > 0 && (
                <div className="flex flex-col gap-1.5 border-t border-brand-border pt-3">
                  {finalBill.breakdown.map((item, i) => (
                    <div key={i} className="flex justify-between text-sm">
                      <span className="text-text-secondary">{item.label}</span>
                      <span className={item.amount < 0 ? 'text-status-success' : 'text-text-muted'}>
                        {item.amount < 0 ? '−' : ''}${Math.abs(item.amount).toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-text-secondary text-xs mt-3">
                Effective next billing cycle · {newPlanName}
              </p>
            </div>
          )}

          <div className="card">
            <p className="section-label mb-3">What's next</p>
            <div className="flex flex-col gap-2.5">
              {[
                { when: 'Tonight',   what: `Snapshot sent to ${customer.phone}` },
                { when: 'Next bill', what: `Reflects ${newPlanName} and any credits` },
                { when: 'Questions', what: 'Call 611 or visit any T-Mobile store' },
              ].map(item => (
                <div key={item.when} className="flex gap-3 items-baseline">
                  <span className="text-magenta text-xs font-semibold w-20 flex-shrink-0">{item.when}</span>
                  <span className="text-text-muted text-sm">{item.what}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card-dark grid grid-cols-2 gap-3">
            <div>
              <p className="text-text-secondary text-xs">Name</p>
              <p className="text-white text-sm font-medium">{customer.name}</p>
            </div>
            <div>
              <p className="text-text-secondary text-xs">Account</p>
              <p className="text-white text-sm font-medium">{customer.account_id}</p>
            </div>
            <div>
              <p className="text-text-secondary text-xs">Plan</p>
              <p className="text-white text-sm font-medium">{newPlanName}</p>
            </div>
            <div>
              <p className="text-text-secondary text-xs">Lines</p>
              <p className="text-white text-sm font-medium">{customer.current_plan?.lines}</p>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setEmailSent(true)}
              disabled={emailSent}
              className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-semibold border transition-all ${
                emailSent
                  ? 'border-status-success text-status-success bg-status-success/10'
                  : 'border-brand-border-light text-white hover:border-magenta hover:text-magenta'
              }`}
            >
              {emailSent
                ? <><CheckCircle2 size={14} /> Sent</>
                : <><Mail size={14} /> Email to customer</>}
            </button>
            <button
              onClick={onNewVisit}
              className="flex-1 bg-magenta hover:bg-magenta-hover text-white font-semibold py-3 rounded-lg transition-all active:scale-95 text-sm flex items-center justify-center gap-2"
            >
              <RefreshCw size={14} />
              New Visit
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
