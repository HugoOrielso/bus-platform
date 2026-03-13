// src/server.ts
import 'dotenv/config'
import http from 'http'
import express from 'express'
import cors from 'cors'
import morgan from 'morgan'
import { WebSocketServer, WebSocket } from 'ws'
import { URL } from 'url'
import { errorHandler } from './middlewares/error.middleware'
import { wsService } from './services/websocket/websocket.service'
import authRouter from './router/auth.routes'
import busesRouter from './router/buses.routes'
import rutasRouter from './router/routes.routes'
import { jwtService } from './services/jwt/jwt.services'
import viajesRouter from './router/travels.routes'
import reportesRouter from './router/reports.route'

const app = express()
const server = http.createServer(app)

app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
}))
app.use(express.json())
app.use(morgan(process.env.NODE_ENV === 'development' ? 'dev' : 'combined'))

// ─── RUTAS HTTP ──────────────────────────────────────────
app.use('/api/auth', authRouter)
app.use('/api/buses', busesRouter)
app.use('/api/rutas', rutasRouter)
app.use('/api/viajes', viajesRouter)
app.use('/api/reportes', reportesRouter)

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString(), version: '1.0.0' })
})

// ─── WEBSOCKET SERVER ────────────────────────────────────
// El cliente se conecta a:
//   ws://localhost:4000/ws/viaje/:id?token=ACCESS_TOKEN
//   ws://localhost:4000/ws/dashboard?token=ACCESS_TOKEN

const wss = new WebSocketServer({ noServer: true })

server.on('upgrade', (request, socket, head) => {
  const { pathname, searchParams } = new URL(request.url!, `http://${request.headers.host}`)

  // Verificar JWT en query param
  const token = searchParams.get('token')
  if (!token) {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
    socket.destroy()
    return
  }

  try {
    jwtService.verifyAccess(token)
  } catch {
    socket.write('HTTP/1.1 401 Unauthorized\r\n\r\n')
    socket.destroy()
    return
  }

  if (pathname.startsWith('/ws/')) {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request, pathname)
    })
  } else {
    socket.destroy()
  }
})

wss.on('connection', (socket: WebSocket, _request: http.IncomingMessage, pathname: string) => {
  // Determinar roomId desde la URL
  let roomId: string

  if (pathname === '/ws/dashboard') {
    roomId = '__dashboard__'
  } else {
    // /ws/viaje/:id
    const match = pathname.match(/^\/ws\/viaje\/(.+)$/)
    if (!match) { socket.close(); return }
    roomId = match[1]
  }

  wsService.join(roomId, socket)

  socket.send(JSON.stringify({
    type: 'PONG',
    payload: { message: `Conectado a "${roomId}"`, stats: wsService.stats() },
  }))

  socket.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString())
      if (msg.type === 'PING') {
        socket.send(JSON.stringify({ type: 'PONG', payload: { ts: new Date().toISOString() } }))
      }
    } catch { /* ignorar */ }
  })

  socket.on('close', () => wsService.leave(roomId, socket))
  socket.on('error', (err) => console.error('[WS Error]', err.message))
})

// ─── ERROR HANDLER ───────────────────────────────────────
app.use(errorHandler)

// ─── INICIAR SERVIDOR ────────────────────────────────────
const PORT = parseInt(process.env.PORT || '4000')

server.listen(PORT, () => {
  console.log('\n🚌 Bus Platform API')
  console.log(`   HTTP  → http://localhost:${PORT}`)
  console.log(`   WS    → ws://localhost:${PORT}/ws/viaje/:id?token=TU_TOKEN`)
  console.log(`   WS    → ws://localhost:${PORT}/ws/dashboard?token=TU_TOKEN`)
  console.log(`   Health → http://localhost:${PORT}/health\n`)
})

export default app