import { useState, useEffect } from 'react'
import tmoLogo from './assets/tmo-logo.svg'
import CustomerLookup from './components/lookup/CustomerLookup.jsx'
import CustomerBrief from './components/brief/CustomerBrief.jsx'
import BillExplorer from './components/brief/BillExplorer.jsx'
import ConversationListener from './components/listener/ConversationListener.jsx'
import PAHPanel from './components/listener/PAHPanel.jsx'
import ExecutionScreen from './components/execute/ExecutionScreen.jsx'
import CommitmentSnapshot from './components/CommitmentSnapshot.jsx'

function LiveClock() {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return <span>{time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
}

export default function App() {
  const [customer, setCustomer] = useState(null)
  const [brief, setBrief] = useState(null)
  const [pahStatus, setPahStatus] = useState(null)
  const [pendingTransaction, setPendingTransaction] = useState(null)
  const [detectedIntent, setDetectedIntent] = useState(null)
  const [executionResult, setExecutionResult] = useState(null)

  function handleNewVisit() {
    setCustomer(null)
    setBrief(null)
    setPahStatus(null)
    setPendingTransaction(null)
    setDetectedIntent(null)
    setExecutionResult(null)
  }

  return (
    <div className="min-h-screen bg-black text-white font-sans flex flex-col">

      {/* Magenta accent bar — the brand cue that reads before any text does. */}
      <div className="h-[3px] w-full bg-magenta-gradient flex-shrink-0" />

      <header
        className="bg-black border-b border-brand-border px-6 flex items-center justify-between flex-shrink-0"
        style={{ height: '60px' }}
      >
        <div className="flex items-center gap-5">
          <img src={tmoLogo} alt="T-Mobile" className="h-9 w-9 flex-shrink-0" />
          <div className="h-7 w-px bg-brand-border" />
          <div className="flex flex-col justify-center">
            <span className="text-white font-bold text-base leading-tight tracking-tight">T-Rep AI</span>
            <span className="text-text-secondary text-[11px] leading-tight tracking-wide uppercase">
              Store Representative Co-Pilot
            </span>
          </div>
        </div>

        <div className="flex items-center gap-5">
          {/* Who the rep is currently serving, so it stays visible while they
              scroll a long brief. */}
          {customer && (
            <div className="flex items-center gap-2 border-l border-brand-border pl-5">
              <span className="w-2 h-2 rounded-full bg-status-success flex-shrink-0" />
              <div className="flex flex-col">
                <span className="text-white text-xs font-semibold leading-tight">{customer.name}</span>
                <span className="text-text-secondary text-[11px] leading-tight">{customer.account_id}</span>
              </div>
            </div>
          )}
          <div className="text-text-secondary text-xs font-mono tabular-nums border-l border-brand-border pl-5">
            <LiveClock />
          </div>
        </div>
      </header>

      <div className="flex-1">
        {executionResult ? (
          <CommitmentSnapshot
            customer={customer}
            brief={brief}
            transaction={pendingTransaction}
            finalBill={executionResult}
            onNewVisit={handleNewVisit}
          />
        ) : (
          <main className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-12 gap-6">
            <div className="col-span-4 flex flex-col gap-4">
              <CustomerLookup onCustomerLoaded={(c, b, p) => { setCustomer(c); setBrief(b); setPahStatus(p) }} />
              {customer && brief && (
                <CustomerBrief customer={customer} brief={brief} />
              )}
              {pahStatus && !pahStatus.is_authorized && (
                <PAHPanel pahStatus={pahStatus} />
              )}
            </div>

            <div className="col-span-5 flex flex-col gap-4">
              {customer && (
                <>
                  <BillExplorer customer={customer} detectedIntent={detectedIntent} onConfirm={setPendingTransaction} />
                  <ConversationListener customer={customer} onIntentDetected={setDetectedIntent} />
                </>
              )}
            </div>

            <div className="col-span-3">
              {pendingTransaction && (
                <ExecutionScreen
                  transaction={pendingTransaction}
                  customer={customer}
                  onComplete={setExecutionResult}
                />
              )}
            </div>
          </main>
        )}
      </div>

      {!executionResult && (
        <footer className="border-t border-brand-border px-6 py-2.5 flex items-center justify-between flex-shrink-0">
          <span className="text-text-secondary text-xs">
            © 2026 T-Mobile USA, Inc. Internal Tool — Not for Customer Distribution
          </span>
          <div className="flex items-center gap-4 text-text-secondary text-xs">
            <span>T-Rep AI v1.0</span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success" />
              Systems Operational
            </span>
          </div>
        </footer>
      )}
    </div>
  )
}
