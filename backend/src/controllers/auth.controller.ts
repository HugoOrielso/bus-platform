// src/controllers/auth.controller.ts
import { Request, Response } from 'express'
import bcrypt from 'bcrypt'
import { z } from 'zod'
import { AuthRequest } from '../types'
import { prisma } from '../database/db.database'
import { jwtService } from '../services/jwt/jwt.services'

const registerSchema = z.object({
  nombre: z.string().min(2, 'Nombre muy corto'),
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
  rol: z.enum(['ADMIN', 'OPERADOR', 'SUPERVISOR']).optional(),
})

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

export const authController = {
  async register(req: Request, res: Response) {
    const result = registerSchema.safeParse(req.body)
    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    const { nombre, email, password, rol } = result.data

    const existe = await prisma.user.findUnique({ where: { email } })
    if (existe) return res.status(409).json({ error: 'El email ya está registrado' })

    const hash = await bcrypt.hash(password, 10)
    const user = await prisma.user.create({
      data: { nombre, email, password: hash, rol: rol ?? 'OPERADOR' },
      select: { id: true, nombre: true, email: true, rol: true, createdAt: true },
    })

    return res.status(201).json({ message: 'Usuario creado', data: user })
  },

  async login(req: Request, res: Response) {
    const result = loginSchema.safeParse(req.body)
    if (!result.success) {
      return res.status(400).json({ error: 'Datos inválidos' })
    }

    const { email, password } = result.data

    const user = await prisma.user.findUnique({ where: { email } })
    if (!user || !user.activo) {
      return res.status(401).json({ error: 'Credenciales incorrectas' })
    }

    const passwordOk = await bcrypt.compare(password, user.password)
    if (!passwordOk) {
      return res.status(401).json({ error: 'Credenciales incorrectas' })
    }

    const payload = { userId: user.id, email: user.email, rol: user.rol }
    const accessToken = jwtService.signAccess(payload)
    const refreshToken = jwtService.signRefresh(payload)

    await prisma.refreshToken.create({
      data: {
        token: refreshToken,
        userId: user.id,
        expiresAt: jwtService.refreshExpiresAt(),
      },
    })

    return res.json({
      accessToken,
      refreshToken,
      user: { id: user.id, nombre: user.nombre, email: user.email, rol: user.rol },
    })
  },

  async refresh(req: Request, res: Response) {
    const { refreshToken } = req.body
    if (!refreshToken) {
      return res.status(400).json({ error: 'Refresh token requerido' })
    }

    try {
      const payload = jwtService.verifyRefresh(refreshToken)

      const stored = await prisma.refreshToken.findUnique({ where: { token: refreshToken } })
      if (!stored || stored.expiresAt < new Date()) {
        return res.status(401).json({ error: 'Refresh token inválido o expirado' })
      }

      const newAccessToken = jwtService.signAccess({
        userId: payload.userId,
        email: payload.email,
        rol: payload.rol,
      })

      return res.json({ accessToken: newAccessToken })
    } catch {
      return res.status(401).json({ error: 'Refresh token inválido' })
    }
  },

  async logout(req: AuthRequest, res: Response) {
    const { refreshToken } = req.body
    if (refreshToken) {
      await prisma.refreshToken.deleteMany({ where: { token: refreshToken } })
    }
    return res.json({ message: 'Sesión cerrada correctamente' })
  },

  async me(req: AuthRequest, res: Response) {
    const user = await prisma.user.findUnique({
      where: { id: req.user!.userId },
      select: { id: true, nombre: true, email: true, rol: true, activo: true, createdAt: true },
    })
    if (!user) return res.status(404).json({ error: 'Usuario no encontrado' })
    return res.json({ data: user })
  },
}