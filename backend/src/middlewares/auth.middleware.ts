// src/middlewares/auth.middleware.ts
import { Response, NextFunction } from 'express'
import { AuthRequest, JwtPayload } from '../types'
import { jwtService } from '../services/jwt/jwt.services'

// Verifica que el access token sea válido
export function authenticate(req: AuthRequest, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Token requerido' })
  }

  const token = authHeader.split(' ')[1]

  try {
    const payload = jwtService.verifyAccess(token)
    req.user = payload
    next()
  } catch {
    return res.status(401).json({ error: 'Token inválido o expirado' })
  }
}

// Verifica que el usuario tenga uno de los roles permitidos
export function authorize(...roles: JwtPayload['rol'][]) {
  return (req: AuthRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'No autenticado' })
    }
    if (!roles.includes(req.user.rol)) {
      return res.status(403).json({ error: 'No tienes permisos para esta acción' })
    }
    next()
  }
}