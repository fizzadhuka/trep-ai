import { useState, useRef, useCallback } from 'react'
import { createClient, LiveTranscriptionEvents } from '@deepgram/sdk'

export function useDeepgram({ onTranscript } = {}) {
  const [isListening, setIsListening] = useState(false)
  const connectionRef = useRef(null)
  const recorderRef = useRef(null)

  const start = useCallback(async (apiKey) => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const deepgram = createClient(apiKey)
    const connection = deepgram.listen.live({
      model: 'nova-2',
      language: 'en-US',
      smart_format: true,
      interim_results: true,
    })

    connection.on(LiveTranscriptionEvents.Transcript, (data) => {
      const transcript = data?.channel?.alternatives?.[0]?.transcript
      if (transcript && data.is_final && onTranscript) {
        onTranscript(transcript)
      }
    })

    connection.on(LiveTranscriptionEvents.Open, () => {
      const recorder = new MediaRecorder(stream)
      recorder.ondataavailable = (e) => connection.send(e.data)
      recorder.start(250)
      recorderRef.current = recorder
      setIsListening(true)
    })

    connectionRef.current = connection
  }, [onTranscript])

  const stop = useCallback(() => {
    recorderRef.current?.stop()
    connectionRef.current?.finish()
    setIsListening(false)
  }, [])

  return { isListening, start, stop }
}
