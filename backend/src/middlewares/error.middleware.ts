// src/middlewares/error.middleware.ts
import { Request, Response, NextFunction } from 'express'

export class AppError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message)
    this.name = 'AppError'
  }
}

export function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction) {
  console.error(`[ERROR] ${err.message}`)

  if (err instanceof AppError) {
    return res.status(err.statusCode).json({ error: err.message })
  }

  // Error de Prisma: registro no encontrado
  if (err.message?.includes('Record to update not found')) {
    return res.status(404).json({ error: 'Registro no encontrado' })
  }

  // Error de Prisma: unique constraint
  if (err.message?.includes('Unique constraint')) {
    return res.status(409).json({ error: 'Ya existe un registro con esos datos' })
  }

  return res.status(500).json({ error: 'Error interno del servidor' })
}