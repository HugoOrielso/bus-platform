// src/services/jwt.service.ts
import jwt from 'jsonwebtoken'
import { JwtPayload } from '../types'

const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET!
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET!
const ACCESS_EXPIRES = process.env.JWT_ACCESS_EXPIRES || '15m'
const REFRESH_EXPIRES = process.env.JWT_REFRESH_EXPIRES || '7d'

export const jwtService = {
  signAccess(payload: JwtPayload): string {
    return jwt.sign(payload, ACCESS_SECRET, { expiresIn: ACCESS_EXPIRES } as jwt.SignOptions)
  },

  signRefresh(payload: JwtPayload): string {
    return jwt.sign(payload, REFRESH_SECRET, { expiresIn: REFRESH_EXPIRES } as jwt.SignOptions)
  },

  verifyAccess(token: string): JwtPayload {
    return jwt.verify(token, ACCESS_SECRET) as JwtPayload
  },

  verifyRefresh(token: string): JwtPayload {
    return jwt.verify(token, REFRESH_SECRET) as JwtPayload
  },

  // Calcula fecha de expiración del refresh token para guardar en DB
  refreshExpiresAt(): Date {
    const days = parseInt(REFRESH_EXPIRES.replace('d', '')) || 7
    const date = new Date()
    date.setDate(date.getDate() + days)
    return date
  },
}