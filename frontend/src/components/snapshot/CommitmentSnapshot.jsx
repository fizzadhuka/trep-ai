import { useState } from 'react'

function formatDate() {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
}

export default function CommitmentSnapshot({ customer, brief, transaction, finalBill, onNewVisit }) {
  const [emailSent, setEmailSent] = useState(false)

  const transactionLabel = transaction?.transaction_type?.replace(/_/g, ' ') || 'Account update'
  const previousTotal = customer.current_plan?.monthly_total
  const newTotal = finalBill?.new_monthly_total
  const delta = newTotal != null && previousTotal != null ? newTotal - previousTotal : null

  return (
    <div className="max-w-2xl mx-auto px-6 py-8 flex flex-col gap-5">
      <div className="bg-tmobile-magenta rounded-xl p-5">
        <p className="text-white/70 text-xs uppercase tracking-wider mb-1">Visit Complete · {formatDate()}</p>
        <h1 className="text-white font-bold text-2xl">Your Commitment Snapshot</h1>
        <p className="text-white/80 text-sm mt-1">Everything discussed and completed today, {customer.name.split(' ')[0]}.</p>
      </div>

      {brief && !brief.parse_error && (
        <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-4">
          <p className="text-tmobile-gray text-xs uppercase tracking-wider mb-2">Your Visit, In Plain English</p>
          <p className="text-zinc-300 text-sm leading-relaxed">{brief.plan_summary}</p>
          {brief.upgrade_status && <p className="text-zinc-400 text-sm mt-1">{brief.upgrade_status}</p>}
        </div>
      )}

      {transaction && (
        <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-4">
          <p className="text-tmobile-gray text-xs uppercase tracking-wider mb-3">What Changed Today</p>
          <div className="flex flex-col gap-2">
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-tmobile-magenta mt-1.5 flex-shrink-0" />
              <div>
                <p className="text-white text-sm font-medium capitalize">{transactionLabel}</p>
                {transaction.params?.proposed_plan && (
                  <p className="text-zinc-400 text-xs mt-0.5">{customer.current_plan?.name} → {transaction.params.proposed_plan}</p>
                )}
              </div>
            </div>
            {finalBill?.promo_applied && (
              <div className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 mt-1.5 flex-shrink-0" />
                <p className="text-green-400 text-sm">Promo applied: {finalBill.promo_applied}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {finalBill && (
        <div className="bg-zinc-900 border border-green-500/30 rounded-xl p-4">
          <p className="text-tmobile-gray text-xs uppercase tracking-wider mb-3">Your New Monthly Bill</p>
          {finalBill.breakdown?.map((item, i) => (
            <div key={i} className="flex justify-between text-sm mb-1.5">
              <span className="text-zinc-400">{item.label}</span>
              <span className={item.amount < 0 ? 'text-green-400' : 'text-zinc-300'}>
                {item.amount < 0 ? '-' : ''}${Math.abs(item.amount).toFixed(2)}
              </span>
            </div>
          ))}
          <div className="border-t border-zinc-700 pt-3 mt-3 flex justify-between items-baseline">
            <div>
              <span className="text-tmobile-magenta font-bold text-3xl">${newTotal}/mo</span>
              {previousTotal != null && delta !== 0 && (
                <span className={`text-xs ml-2 ${delta < 0 ? 'text-green-400' : 'text-zinc-400'}`}>(was ${previousTotal})</span>
              )}
            </div>
            {delta != null && delta < 0 && (
              <span className="text-green-400 text-sm font-semibold">Save ${Math.abs(delta)}/mo · ${Math.abs(delta) * 12}/yr</span>
            )}
          </div>
        </div>
      )}

      <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-4">
        <p className="text-tmobile-gray text-xs uppercase tracking-wider mb-3">What to Expect Next</p>
        <div className="flex flex-col gap-3">
          {[
            { when: 'Tonight', what: `A copy of this snapshot will be sent to ${customer.phone}` },
            { when: 'Next cycle', what: "Your updated bill will reflect today's changes" },
            { when: 'Any time', what: 'Contact T-Mobile if anything differs from what was discussed today' },
          ].map((item) => (
            <div key={item.when} className="flex gap-3">
              <span className="text-tmobile-magenta text-xs font-semibold w-20 flex-shrink-0 pt-0.5">{item.when}</span>
              <span className="text-zinc-400 text-sm">{item.what}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-zinc-800 rounded-xl p-4 grid grid-cols-2 gap-3">
        <div>
          <p className="text-tmobile-gray text-xs uppercase tracking-wider mb-1">Customer</p>
          <p className="text-white text-sm font-medium">{customer.name}</p>
          <p className="text-zinc-400 text-xs">{customer.phone}</p>
        </div>
        <div>
          <p className="text-tmobile-gray text-xs uppercase tracking-wider mb-1">Account</p>
          <p className="text-white text-sm font-medium">{customer.account_id}</p>
          <p className="text-zinc-400 text-xs">{transaction?.params?.proposed_plan || customer.current_plan?.name}</p>
        </div>
      </div>

      <div className="flex gap-3 pb-6">
        <button
          onClick={() => setEmailSent(true)}
          disabled={emailSent}
          className="flex-1 border border-zinc-600 hover:border-tmobile-magenta text-white disabled:text-green-400 disabled:border-green-500/40 text-sm font-semibold py-3 rounded-lg transition-colors"
        >
          {emailSent ? '✓ Snapshot sent' : 'Email to customer'}
        </button>
        <button
          onClick={onNewVisit}
          className="flex-1 bg-tmobile-magenta hover:bg-tmobile-berry text-white text-sm font-semibold py-3 rounded-lg transition-colors"
        >
          New Visit
        </button>
      </div>
    </div>
  )
}
