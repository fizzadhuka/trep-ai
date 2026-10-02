import { useState, useRef } from 'react'
import { Mic, MicOff, MessageSquare, Zap, Send } from 'lucide-react'
import { useTranscription } from '../../hooks/useTranscription.js'
import { api } from '../../services/api.js'

// One line of next-best-action per topic, keyed to the topics IntentAgent
// returns. Retail reps read this between sentences, so it stays short.
const REP_GUIDANCE = {
  plan_upgrade:   'Confirm the plan, then walk through what changes on their bill.',
  trade_in:       'Quote the trade-in value before naming the new device price.',
  device_inquiry: 'Lead with monthly cost after trade-in, not sticker price.',
  add_line:       'Verify they are the account holder before adding a line.',
  billing:        'Resolve the charge first — hold any upsell until it is settled.',
  complaint:      'Acknowledge and resolve. Do not pitch anything yet.',
  downgrade:      'Check retention offers before reducing their plan.',
}

export default function ConversationListener({ customer, onIntentDetected }) {
  const [transcript, setTranscript] = useState([])
  const [intent, setIntent] = useState(null)
  const [manualInput, setManualInput] = useState('')
  const scrollRef = useRef(null)

  // A priced result is the strongest possible signal the intent was understood
  // — BillAgent only returns a number when it resolved a real plan, device, or
  // line change. Gating those behind a confidence score throws away the one
  // case that matters most, since the model reports low confidence on perfectly
  // clear speech often enough to drop it mid-demo.
  function acceptIntent(result) {
    if (!result || result.topic === 'none') return
    const priced = result.data_to_surface?.bill_delta != null
    if (priced || (result.confidence ?? 0) >= 0.5) {
      setIntent(result)
      onIntentDetected(result)
    }
  }

  function appendLine(text) {
    setTranscript(prev => [...prev, text])
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }

  // Mic path: /transcribe returns transcript AND intent in one round trip,
  // so there's no second call to make here.
  function handleMicResult({ text, intent: detected }) {
    appendLine(text)
    acceptIntent(detected)
  }

  // Typed path: no audio, so intent has to be requested separately.
  async function handleTypedTranscript(text) {
    appendLine(text)
    acceptIntent(await api.detectIntent(customer.account_id, text))
  }

  const { isListening, isProcessing, error, start, stop } = useTranscription({
    customerId: customer.account_id,
    onResult: handleMicResult,
  })

  async function handleManualSubmit(e) {
    e.preventDefault()
    if (!manualInput.trim()) return
    await handleTypedTranscript(manualInput)
    setManualInput('')
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <MessageSquare size={13} className="text-text-secondary" />
          <p className="section-label">Conversation</p>
          {isListening && (
            <span className="flex items-center gap-1 text-xs text-status-success font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
              Live
            </span>
          )}
        </div>

        <button
          onClick={() => (isListening ? stop() : start())}
          className={`flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all ${
            isListening
              ? 'bg-status-error/10 border-status-error/40 text-status-error hover:bg-status-error/20'
              : 'bg-magenta/10 border-magenta/40 text-magenta hover:bg-magenta/20'
          }`}
        >
          {isListening ? <MicOff size={13} /> : <Mic size={13} />}
          {isListening ? (isProcessing ? 'Transcribing' : 'Stop') : 'Start mic'}
        </button>
      </div>

      {error && (
        <div className="bg-status-error/10 border border-status-error/30 rounded-lg px-3 py-2 mb-3">
          <p className="text-status-error text-xs">Mic error: {error}</p>
        </div>
      )}

      {intent && (
        <div className="bg-magenta/5 border border-magenta/30 rounded-lg px-3 py-2.5 mb-3 animate-fade-in">
          <div className="flex items-center justify-between gap-2">
            <p className="text-magenta text-xs font-semibold capitalize flex items-center gap-1.5">
              <Zap size={11} className="flex-shrink-0" />
              {intent.topic.replace(/_/g, ' ')}
            </p>
            {intent.confidence != null && (
              <span className="text-text-secondary text-xs tabular-nums">
                {Math.round(intent.confidence * 100)}%
              </span>
            )}
          </div>

          {/* What the rep should do about it. The raw `details` object was
              never meant for display — its keys change from run to run. */}
          {REP_GUIDANCE[intent.topic] && (
            <p className="text-text-muted text-xs mt-1.5 leading-relaxed">{REP_GUIDANCE[intent.topic]}</p>
          )}

          {intent.data_to_surface?.bill_delta && (
            <p className="text-white text-xs font-semibold mt-2 flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-magenta flex-shrink-0" />
              Priced automatically — see Bill explorer
            </p>
          )}
        </div>
      )}

      <div
        ref={scrollRef}
        className="bg-brand-card border border-brand-border rounded-lg p-3 h-36 overflow-y-auto flex flex-col gap-1.5 mb-3"
      >
        {transcript.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center gap-1">
            <Mic size={18} className="text-text-secondary" />
            <p className="text-text-secondary text-xs">Start the mic or type a phrase below</p>
          </div>
        ) : (
          transcript.map((line, i) => (
            <p key={i} className="text-text-muted text-sm leading-relaxed animate-fade-in">{line}</p>
          ))
        )}
      </div>

      {/* Typed fallback — the demo has to survive a dead mic or a loud room. */}
      <form onSubmit={handleManualSubmit} className="flex gap-2">
        <input
          value={manualInput}
          onChange={e => setManualInput(e.target.value)}
          placeholder="Or type a phrase to simulate..."
          className="flex-1 bg-brand-card border border-brand-border rounded-lg px-3 py-2 text-xs text-white placeholder-text-secondary focus:outline-none focus:border-magenta transition-colors"
        />
        <button
          type="submit"
          disabled={!manualInput.trim()}
          className="text-xs font-semibold bg-brand-border-light hover:bg-magenta text-white px-3 py-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
        >
          <Send size={12} />
          Send
        </button>
      </form>
    </div>
  )
}
