import { useEffect, useRef, useCallback } from 'react'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket(path, { onMessage } = {}) {
  const wsRef = useRef(null)
  const pendingRef = useRef(null)
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}${path}`)
    ws.onopen = () => {
      if (pendingRef.current !== null) {
        ws.send(JSON.stringify(pendingRef.current))
        pendingRef.current = null
      }
    }
    ws.onmessage = (e) => onMessageRef.current?.(JSON.parse(e.data))
    wsRef.current = ws
    return () => ws.close()
  }, [path])

  const send = useCallback((data) => {
    const ws = wsRef.current
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    } else {
      pendingRef.current = data
    }
  }, [])

  return { send }
}
