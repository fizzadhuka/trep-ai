import { useState, useEffect } from 'react'
import { Loader2, ChevronRight } from 'lucide-react'
import { api } from '../../services/api.js'

const PLANS = ['Essentials', 'Magenta', 'Magenta MAX', 'Go5G Plus']

// IntentAgent's `details` keys change from run to run — the backend keeps its
// own list for exactly this reason (services/../intent_agent.py _PLAN_KEYS).
// Checking only `details.plan` means auto-fill silently misses most of the time
// and the rep has to reach for the dropdown mid-conversation.
const PLAN_KEYS = ['plan_name', 'requested_plan', 'target_plan', 'to_plan', 'plan']

function planFromDetails(details = {}) {
  for (const key of PLAN_KEYS) {
    const value = details[key]
    if (typeof value === 'string' && value.trim() && value.toLowerCase() !== 'unknown') {
      const match = PLANS.find(p => p.toLowerCase().includes(value.trim().toLowerCase()))
      if (match) return match
    }
  }
  return null
}

export default function BillExplorer({ customer, detectedIntent, onConfirm }) {
  const [selectedPlan, setSelectedPlan] = useState('')
  const [delta, setDelta] = useState(null)
  const [loading, setLoading] = useState(false)
  // True when the number came from the conversation rather than the dropdown.
  const [fromConversation, setFromConversation] = useState(false)

  // /intent already prices the change when the customer names a plan, a device,
  // or a line count — BillAgent runs server side and the result rides along in
  // data_to_surface.bill_delta. Using it means the number is on screen the
  // moment they finish the sentence, with no second round trip. Re-fetching
  // would also lose device and line changes, which the dropdown can't express.
  useEffect(() => {
    const priced = detectedIntent?.data_to_surface?.bill_delta
    if (priced?.new_monthly_total != null) {
      setDelta(priced)
      setFromConversation(true)
      // Keep the dropdown in sync so the UI doesn't contradict itself.
      const match = PLANS.find(p => p === priced.proposed_plan)
        || planFromDetails(detectedIntent.details)
      if (match) setSelectedPlan(match)
      return
    }

    // Not priced server side — fall back to filling the dropdown so the rep is
    // one click away instead of starting from scratch.
    const guess = planFromDetails(detectedIntent?.details)
    if (guess) setSelectedPlan(guess)
  }, [detectedIntent])

  // Manual dropdown path. Skipped when the conversation already priced this
  // plan, otherwise selecting it would refetch and discard device/line context.
  useEffect(() => {
    if (!selectedPlan || selectedPlan === customer?.current_plan?.name) {
      if (!fromConversation) setDelta(null)
      return
    }
    if (fromConversation && delta?.proposed_plan === selectedPlan) return

    setLoading(true)
    setFromConversation(false)
    api.getBillDelta(customer.account_id, customer.current_plan.name, selectedPlan)
      .then(setDelta)
      .catch(() => setDelta(null))
      .finally(() => setLoading(false))
  }, [selectedPlan]) // eslint-disable-line react-hooks/exhaustive-deps

  const proposedLabel = delta?.proposed_plan || selectedPlan

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <p className="section-label">Bill explorer</p>
        {fromConversation && (
          <span className="flex items-center gap-1.5 text-magenta text-xs font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-magenta animate-pulse" />
            From conversation
          </span>
        )}
      </div>

      <div className="flex gap-2 items-center mb-4">
        <label className="text-text-secondary text-sm whitespace-nowrap">What if I switch to</label>
        <select
          value={selectedPlan}
          onChange={e => setSelectedPlan(e.target.value)}
          className="flex-1 bg-brand-card border border-brand-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-magenta transition-colors"
        >
          <option value="">Select a plan...</option>
          {PLANS.filter(p => p !== customer?.current_plan?.name).map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-text-secondary text-sm">
          <Loader2 size={13} className="animate-spin" />
          Calculating
        </div>
      )}

      {delta && !loading && (
        <div className="card-dark !p-4 flex flex-col gap-2.5 animate-fade-in">

          {/* The new total is the number the rep says out loud, so it gets the
              size. Everything else here is supporting detail. */}
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="section-label mb-1">{proposedLabel}</p>
              <p className="text-white text-3xl font-bold leading-none">
                ${Number(delta.new_monthly_total).toFixed(0)}
                <span className="text-text-secondary text-base font-normal">/mo</span>
              </p>
            </div>
            <div className="text-right">
              <p className="text-text-secondary text-xs line-through">
                ${Number(delta.current_monthly_total).toFixed(0)}/mo now
              </p>
              <p className={`text-sm font-bold mt-0.5 ${
                delta.direction === 'increase' ? 'text-magenta'
                  : delta.direction === 'decrease' ? 'text-status-success'
                  : 'text-text-secondary'
              }`}>
                {delta.direction === 'none'
                  ? 'No change'
                  : `${delta.direction === 'increase' ? '+' : '−'}$${Number(delta.delta_dollars).toFixed(2)}/mo`}
              </p>
            </div>
          </div>

          {/* Line count change — only surfaced when the customer asked for it,
              which the dropdown alone can never express. */}
          {delta.new_lines != null && delta.lines != null && delta.new_lines !== delta.lines && (
            <div className="flex justify-between text-xs border-t border-brand-border pt-2">
              <span className="text-text-secondary">Lines</span>
              <span className="text-white font-medium">{delta.lines} → {delta.new_lines}</span>
            </div>
          )}

          {delta.device && (
            <div className="flex justify-between text-xs">
              <span className="text-text-secondary">Device</span>
              <span className="text-white font-medium">
                {typeof delta.device === 'string' ? delta.device : delta.device.model}
              </span>
            </div>
          )}

          {delta.one_time_credit > 0 && (
            <div className="flex justify-between items-center bg-status-success/10 border border-status-success/20 rounded-lg px-2.5 py-1.5">
              <span className="text-status-success text-xs font-semibold">One-time credit</span>
              <span className="text-status-success font-bold text-sm">
                ${Number(delta.one_time_credit).toFixed(2)}
              </span>
            </div>
          )}

          {delta.promos_applied?.length > 0 && (
            <div className="flex flex-col gap-1">
              {delta.promos_applied.map((promo, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-text-muted">
                  <span className="w-1 h-1 rounded-full bg-magenta mt-1.5 flex-shrink-0" />
                  <span>{typeof promo === 'string' ? promo : promo.name || promo.description}</span>
                </div>
              ))}
            </div>
          )}

          <p className="text-text-muted text-sm leading-relaxed border-t border-brand-border pt-2.5">
            {delta.explanation}
          </p>

          <button
            onClick={() => onConfirm({
              customer_id: customer.account_id,
              transaction_type: 'plan_upgrade_only',
              params: {
                new_monthly_total: delta.new_monthly_total,
                proposed_plan: delta.proposed_plan || selectedPlan,
              },
            })}
            className="mt-1 w-full bg-magenta hover:bg-magenta-hover text-white font-semibold py-2.5 rounded-lg transition-all active:scale-95 text-sm flex items-center justify-center gap-2"
          >
            Execute Upgrade
            <ChevronRight size={15} />
          </button>
        </div>
      )}

      {/* The customer raised a cost question the pricing layer couldn't act on
          — usually "why is my bill higher" with no plan or device named. */}
      {!delta && !loading && detectedIntent?.data_to_surface?.bill_delta_error && (
        <p className="text-text-secondary text-xs">
          Cost question detected, but no plan or device named yet — ask which one they're considering.
        </p>
      )}
    </div>
  )
}
