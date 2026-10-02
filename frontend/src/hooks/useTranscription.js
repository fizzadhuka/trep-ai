import { useCallback, useRef, useState } from 'react'

/**
 * Chunked microphone transcription. Replaces useDeepgram.
 *
 * Deepgram is unreachable on the corporate network — the proxy blocks
 * api.deepgram.com under CATEGORY_DENIED (Generative AI and ML Applications).
 * Audio now goes to our own backend, which forwards it to the T-Mobile gateway's
 * whisper-1. That host is allowlisted, and the API key stays server side.
 *
 * Whisper is batch, not streaming, so there are no interim results. We record
 * fixed-length segments and post each one. Round trip is roughly 1.5-3.5s, so
 * text lands a beat behind the speaker rather than mid-word.
 *
 * Why the recorder restarts every segment instead of using MediaRecorder's
 * timeslice: only the first blob in a timesliced stream carries the WebM
 * header. Later blobs are undecodable on their own and Whisper rejects them.
 * Stopping and restarting yields a complete, standalone file each time. The
 * gap between segments is a few milliseconds.
 *
 *   const { isListening, start, stop, error } = useTranscription({
 *     customerId: customer.account_id,
 *     onResult: ({ text, intent }) => { ... },
 *   })
 */
export function useTranscription({
  customerId,
  onResult,
  chunkSeconds = 4,
} = {}) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState(null)

  const streamRef = useRef(null)
  const recorderRef = useRef(null)
  const timerRef = useRef(null)
  const activeRef = useRef(false)

  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const send = useCallback(
    async (blob) => {
      // ~2KB of WebM is silence. Whisper answers silence with hallucinated
      // filler ("Thank you.", "Bye."), which would fire bogus intents.
      if (blob.size < 2000) return

      const form = new FormData()
      form.append('file', blob, 'chunk.webm')
      if (customerId) form.append('customer_id', String(customerId))

      setIsProcessing(true)
      try {
        const res = await fetch(`${base}/transcribe`, { method: 'POST', body: form })
        if (!res.ok) throw new Error(`transcribe ${res.status}`)

        const data = await res.json()
        if (data.text && onResult) {
          onResult({
            text: data.text,
            intent: data.intent || null,
            durationMs: data.duration_ms,
          })
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setIsProcessing(false)
      }
    },
    [base, customerId, onResult],
  )

  // One segment: record for chunkSeconds, post it, immediately start the next.
  const recordSegment = useCallback(() => {
    if (!activeRef.current || !streamRef.current) return

    const parts = []
    const recorder = new MediaRecorder(streamRef.current, {
      mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm',
    })

    recorder.ondataavailable = (e) => e.data.size > 0 && parts.push(e.data)
    recorder.onstop = () => {
      if (parts.length) send(new Blob(parts, { type: recorder.mimeType }))
      if (activeRef.current) recordSegment()
    }

    recorder.start()
    recorderRef.current = recorder
    timerRef.current = setTimeout(() => {
      if (recorder.state !== 'inactive') recorder.stop()
    }, chunkSeconds * 1000)
  }, [chunkSeconds, send])

  const start = useCallback(async () => {
    setError(null)
    try {
      streamRef.current = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      })
      activeRef.current = true
      setIsListening(true)
      recordSegment()
    } catch (err) {
      // Denied permission, or no input device.
      setError(err.message)
      setIsListening(false)
    }
  }, [recordSegment])

  const stop = useCallback(() => {
    activeRef.current = false
    clearTimeout(timerRef.current)

    if (recorderRef.current?.state !== 'inactive') recorderRef.current?.stop()

    // Releasing the tracks is what turns off the browser's recording
    // indicator. Without it the tab looks like it is still listening.
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null

    setIsListening(false)
  }, [])

  return { isListening, isProcessing, error, start, stop }
}
