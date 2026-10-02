const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json()
}

// Multipart — must NOT set Content-Type, the browser adds the boundary itself.
async function postAudio(blob, customerId) {
  const form = new FormData()
  form.append('file', blob, 'chunk.webm')
  if (customerId) form.append('customer_id', String(customerId))
  const res = await fetch(`${BASE}/transcribe`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`API ${res.status}: /transcribe`)
  return res.json()
}

export const api = {
  searchCustomer:  (q) => req(`/customer/search?q=${encodeURIComponent(q)}`),
  transcribe:      postAudio,
  getCustomer:     (id) => req(`/customer/${id}`),
  getCustomerBrief:(id) => req(`/brief/${id}`),
  getBillDelta:    (id, currentPlan, proposedChange) =>
    req('/bill-delta', { method: 'POST', body: JSON.stringify({ customer_id: id, current_plan: currentPlan, proposed_change: proposedChange }) }),
  detectIntent:    (customerId, transcript) =>
    req('/intent', { method: 'POST', body: JSON.stringify({ customer_id: customerId, transcript }) }),
  pahCheck:        (accountId, visitingUser) =>
    req('/pah-check', { method: 'POST', body: JSON.stringify({ account_id: accountId, visiting_user_name: visitingUser }) }),
  getPromos:       (fromPlan, toPlan) => req(`/customer/promotions?from_plan=${fromPlan}&to_plan=${toPlan}`),
  getTradeIn:      (deviceModel) => req(`/customer/trade-in/${encodeURIComponent(deviceModel)}`),
  simulateExecute: (payload) => req('/execute/simulate', { method: 'POST', body: JSON.stringify(payload) }),
}
