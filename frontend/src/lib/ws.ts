// src/lib/ws.ts
const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:4000/api'

type Listener = (msg: unknown) => void

class WsClient {
  private socket: WebSocket | null = null
  private listeners = new Map<string, Set<Listener>>()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private shouldReconnect = true

  connect(room: string) {
    if (this.socket?.readyState === WebSocket.OPEN) return
    this.shouldReconnect = true

    const token = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null
    const url = `${WS_URL}?room=${room}${token ? `&token=${token}` : ''}`

    this.socket = new WebSocket(url)

    this.socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const room = msg.room ?? '__dashboard__'
        this.listeners.get(room)?.forEach((fn) => fn(msg))
        this.listeners.get('*')?.forEach((fn) => fn(msg))
      } catch {}
    }

    this.socket.onclose = () => {
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => this.connect(room), 3000)
      }
    }

    this.socket.onerror = () => {
      this.socket?.close()
    }
  }

  on(room: string, fn: Listener) {
    if (!this.listeners.has(room)) this.listeners.set(room, new Set())
    this.listeners.get(room)!.add(fn)
    return () => this.listeners.get(room)?.delete(fn)
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    this.socket?.close()
    this.socket = null
  }
}

// Singleton — una sola conexión en toda la app
export const wsClient = new WsClient()