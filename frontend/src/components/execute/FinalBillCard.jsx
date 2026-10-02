import { CheckCircle2 } from 'lucide-react'

export default function FinalBillCard({ finalBill }) {
  return (
    <div className="rounded-xl border border-status-success/30 bg-status-success/5 p-4 animate-slide-up">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle2 size={14} className="text-status-success flex-shrink-0" />
        <p className="text-status-success text-xs font-semibold uppercase tracking-wider">
          Transaction complete
        </p>
      </div>

      {/* Line-by-line so the rep can answer "what am I actually being charged
          for" without opening a second system. */}
      {finalBill.breakdown?.length > 0 && (
        <div className="flex flex-col gap-1.5 mb-3">
          {finalBill.breakdown.map((item, i) => (
            <div key={i} className="flex justify-between text-sm">
              <span className="text-text-secondary">{item.label}</span>
              <span className={item.amount < 0 ? 'text-status-success' : 'text-white'}>
                {item.amount < 0 ? '−' : ''}${Math.abs(item.amount).toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="border-t border-status-success/20 pt-3 flex justify-between items-baseline">
        <span className="text-text-secondary text-sm">New monthly total</span>
        <span className="text-white font-bold text-2xl">
          ${Number(finalBill.new_monthly_total).toFixed(0)}
          <span className="text-text-secondary text-sm font-normal">/mo</span>
        </span>
      </div>

      {finalBill.one_time_credit > 0 && (
        <div className="flex justify-between items-baseline mt-2">
          <span className="text-text-secondary text-xs">One-time credit</span>
          <span className="text-status-success font-semibold text-sm">
            ${Number(finalBill.one_time_credit).toFixed(2)}
          </span>
        </div>
      )}

      {finalBill.promo_applied && (
        <p className="text-status-success text-xs mt-2.5 flex items-start gap-1.5">
          <span className="w-1 h-1 rounded-full bg-status-success mt-1.5 flex-shrink-0" />
          {finalBill.promo_applied}
        </p>
      )}
    </div>
  )
}
