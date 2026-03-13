// src/types/index.ts
import { Request } from 'express'

interface JwtPayload {
  userId: string
  email: string
  rol: 'ADMIN' | 'OPERADOR' | 'SUPERVISOR'
}

interface AuthRequest extends Request {
  user?: JwtPayload
}

interface ConteoEvent {
  viajeId: string
  busId: string
  tipo: 'SUBIDA' | 'BAJADA'
  pasajerosActual: number
  totalSubidas: number
  totalBajadas: number
  timestamp: string
  fuente: 'CAMARA' | 'KINECT' | 'MANUAL'
  confianza?: number
}

interface WsMessage {
  type: 'CONTEO_UPDATE' | 'VIAJE_UPDATE' | 'PONG'
  payload: unknown
}