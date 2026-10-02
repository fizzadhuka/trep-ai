import { useState } from 'react'
import { Search, Phone, AlertCircle, Loader2 } from 'lucide-react'
import { api } from '../../services/api.js'

// Straight from backend/mock/customers.json. Typing a 7-digit account number
// mid-demo is a reliable way to fat-finger it in front of judges, and each of
// these exercises a different branch — non-PAH, open billing issue, no upgrade
// eligibility — so the tag doubles as a reminder of what each one proves.
const DEMO_ACCOUNTS = [
  { phone: '555-019-2000', name: 'Maria Gonzalez', tag: 'Upgrade + billing' },
  { phone: '555-027-1000', name: 'Derek Wu',       tag: 'Upgrade eligible' },
  { phone: '555-038-8000', name: 'Jake Patel',     tag: 'Non-PAH' },
  { phone: '555-041-2000', name: 'Sandra Okafor',  tag: 'Failed payment' },
  { phone: '555-050-3000', name: 'Tom Reyes',      tag: 'Not yet eligible' },
]

export default function CustomerLookup({ onCustomerLoaded }) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function runLookup(rawQuery) {
    const q = (rawQuery ?? query).trim()
    if (!q) return
    setLoading(true)
    setError(null)
    try {
      const results = await api.searchCustomer(q)
      if (!results.length) { setError('No customer found.'); return }
      const customer = results[0]
      const [brief, pahStatus] = await Promise.all([
        api.getCustomerBrief(customer.account_id),
        api.pahCheck(customer.account_id, customer.primary_holder?.name || ''),
      ])
      onCustomerLoaded(customer, brief, pahStatus)
    } catch (err) {
      setError('Lookup failed. Check the account number and try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    runLookup()
  }

  function handleDemoClick(phone) {
    setQuery(phone)
    runLookup(phone)
  }

  return (
    <div className="card">
      <p className="section-label mb-3">Customer lookup</p>

      <form onSubmit={handleSubmit} className="relative mb-3">
        <Phone
          size={15}
          className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none"
        />
        <input
          type="text"
          value={query}
          onChange={e => { setQuery(e.target.value); if (error) setError(null) }}
          placeholder="Phone number or account ID"
          className="input-dark pl-10 pr-28"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-magenta hover:bg-magenta-hover text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100 flex items-center gap-2"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          {loading ? 'Looking up' : 'Look up'}
        </button>
      </form>

      {error && (
        <div className="flex items-center gap-2 text-status-error text-sm mb-3 animate-fade-in">
          <AlertCircle size={14} className="flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="flex items-center gap-3 mb-3">
        <div className="flex-1 h-px bg-brand-border" />
        <span className="text-text-secondary text-[11px] uppercase tracking-wider">or select demo</span>
        <div className="flex-1 h-px bg-brand-border" />
      </div>

      <div className="flex flex-col gap-2">
        {DEMO_ACCOUNTS.map(({ phone, name, tag }) => (
          <button
            key={phone}
            onClick={() => handleDemoClick(phone)}
            disabled={loading}
            className="w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg bg-brand-card border border-brand-border hover:border-magenta transition-all duration-200 group disabled:opacity-40 disabled:cursor-not-allowed text-left"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Phone
                size={13}
                className="text-text-secondary group-hover:text-magenta transition-colors flex-shrink-0"
              />
              <div className="min-w-0">
                <div className="text-white text-sm font-semibold truncate">{name}</div>
                <div className="text-text-secondary text-xs">{phone}</div>
              </div>
            </div>
            <span className="badge-magenta flex-shrink-0 whitespace-nowrap">{tag}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
