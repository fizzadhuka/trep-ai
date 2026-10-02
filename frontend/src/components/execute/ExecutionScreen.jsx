import { useState } from 'react'
import { Shield, ChevronRight, Loader2 } from 'lucide-react'
import StepTracker from './StepTracker.jsx'
import FinalBillCard from './FinalBillCard.jsx'
import { useWebSocket } from '../../hooks/useWebSocket.js'

// Mirrors STEP_DEFINITIONS in backend/services/execution_service.py. Rendered
// as pending rows before the socket opens so the rep sees what is about to
// happen and can back out — an empty panel that suddenly fills is worse.
const STEP_NAMES = {
  trade_in_upgrade: [
    'Verifying account identity',
    'Confirming trade-in value',
    'Applying upgrade promotion',
    'Processing plan change',
    'Entering order into DASH',
    'Generating updated bill',
  ],
  plan_upgrade_only: [
    'Verifying account identity',
    'Checking plan eligibility',
    'Processing plan change',
    'Entering order into DASH',
    'Generating updated bill',
  ],
}

function initSteps(type) {
  return (STEP_NAMES[type] || STEP_NAMES.plan_upgrade_only).map((name, i) => ({
    id: i + 1,
    name,
    status: 'pending',
  }))
}

const TRANSACTION_LABELS = {
  trade_in_upgrade:  'Trade-in + plan upgrade',
  plan_upgrade_only: 'Plan upgrade',
}

export default function ExecutionScreen({ transaction, customer, onComplete }) {
  const [confirmed, setConfirmed] = useState(false)
  const [steps, setSteps] = useState(initSteps(transaction.transaction_type))
  const [finalBill, setFinalBill] = useState(null)
  const [running, setRunning] = useState(false)

  const { send } = useWebSocket('/ws/execute', {
    onMessage(msg) {
      if (msg.type === 'step') {
        setSteps(prev => prev.map(s =>
          s.id === msg.id ? { ...s, status: msg.status, message: msg.message } : s
        ))
      } else if (msg.type === 'done') {
        setFinalBill(msg.final_bill)
        setRunning(false)
        // Hands the result to App so it can swap in CommitmentSnapshot. Without
        // this the steps all complete and the flow simply stops here.
        onComplete?.(msg.final_bill)
      } else if (msg.type === 'error') {
        setRunning(false)
      }
    },
  })

  function handleConfirm() {
    setConfirmed(true)
    setRunning(true)
    send({
      customer_id: transaction.customer_id,
      transaction_type: transaction.transaction_type,
      params: transaction.params,
    })
  }

  const completedCount = steps.filter(s => s.status === 'complete').length
  const progressPct = (completedCount / steps.length) * 100
  const activeStep = steps.find(s => s.status === 'active' || s.status === 'retrying')

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <p className="section-label">Execution</p>
        {running && (
          <span className="text-magenta text-xs font-bold tabular-nums">
            {Math.round(progressPct)}%
          </span>
        )}
      </div>

      {!confirmed && (
        <div className="flex flex-col gap-3">
          <div className="card-dark !p-3">
            <p className="section-label mb-1.5">Transaction</p>
            <p className="text-white font-semibold text-sm">
              {TRANSACTION_LABELS[transaction.transaction_type] || transaction.transaction_type}
            </p>

            {transaction.params?.proposed_plan && (
              <div className="flex items-center gap-2 text-xs text-text-secondary mt-2">
                <span>{customer?.current_plan?.name}</span>
                <span className="text-magenta">→</span>
                <span className="text-white font-medium">{transaction.params.proposed_plan}</span>
              </div>
            )}

            {transaction.params?.new_monthly_total != null && (
              <div className="flex items-baseline justify-between mt-2 pt-2 border-t border-brand-border">
                <span className="text-text-secondary text-xs">New monthly</span>
                <span className="text-magenta font-bold text-lg">
                  ${Number(transaction.params.new_monthly_total).toFixed(0)}
                  <span className="text-text-secondary text-xs font-normal">/mo</span>
                </span>
              </div>
            )}
          </div>

          {/* Every step writes to a real account, so it stays behind an
              explicit confirmation rather than firing on selection. */}
          <div className="flex items-start gap-2 text-text-secondary text-xs">
            <Shield size={13} className="text-magenta flex-shrink-0 mt-0.5" />
            <span>
              {steps.length} actions will run on {customer?.name?.split(' ')[0] || 'this account'}.
              Nothing is written until you confirm.
            </span>
          </div>

          <button
            onClick={handleConfirm}
            className="w-full bg-magenta hover:bg-magenta-hover text-white font-semibold py-2.5 rounded-lg transition-all active:scale-95 text-sm flex items-center justify-center gap-2"
          >
            Confirm &amp; Execute
            <ChevronRight size={15} />
          </button>
        </div>
      )}

      {confirmed && (
        <div className="flex flex-col gap-3 animate-fade-in">

          {running && (
            <>
              <div className="w-full bg-brand-border h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-magenta rounded-full transition-all duration-500"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              {activeStep && (
                <div className="flex items-center gap-2 text-text-secondary text-xs">
                  <Loader2 size={12} className="animate-spin text-magenta flex-shrink-0" />
                  {activeStep.name}
                </div>
              )}
            </>
          )}

          <StepTracker steps={steps} />

          {finalBill && <FinalBillCard finalBill={finalBill} />}
        </div>
      )}
    </div>
  )
}
