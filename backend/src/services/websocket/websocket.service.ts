// src/services/websocket.service.ts
import { WebSocket } from 'ws'
import { ConteoEvent, WsMessage } from '../../types'

// Map de viajeId → conjunto de sockets suscritos
const rooms = new Map<string, Set<WebSocket>>()

export const wsService = {
  join(roomId: string, socket: WebSocket) {
    if (!rooms.has(roomId)) rooms.set(roomId, new Set())
    rooms.get(roomId)!.add(socket)
    console.log(`📡 [WS] Cliente unido a room "${roomId}" (total: ${rooms.get(roomId)!.size})`)
  },

  leave(roomId: string, socket: WebSocket) {
    rooms.get(roomId)?.delete(socket)
    if (rooms.get(roomId)?.size === 0) rooms.delete(roomId)
  },

  emit(roomId: string, message: WsMessage) {
    const sockets = rooms.get(roomId)
    if (!sockets?.size) return
    const data = JSON.stringify(message)
    sockets.forEach((ws) => {
      if (ws.readyState === WebSocket.OPEN) ws.send(data)
    })
  },

  emitConteo(event: ConteoEvent) {
    // Emitir al room del viaje específico
    this.emit(event.viajeId, { type: 'CONTEO_UPDATE', payload: event })
    // Emitir también al dashboard global
    this.emit('__dashboard__', { type: 'CONTEO_UPDATE', payload: event })
  },

  broadcast(message: WsMessage) {
    const data = JSON.stringify(message)
    rooms.forEach((sockets) => {
      sockets.forEach((ws) => {
        if (ws.readyState === WebSocket.OPEN) ws.send(data)
      })
    })
  },

  stats() {
    let clientes = 0
    rooms.forEach((s) => (clientes += s.size))
    return { rooms: rooms.size, clientes }
  },
}