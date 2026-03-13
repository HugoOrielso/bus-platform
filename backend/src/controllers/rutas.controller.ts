// src/controllers/rutas.controller.ts
import { Request, Response } from 'express'
import { z } from 'zod'
import { prisma } from '../database/db.database'

const rutaSchema = z.object({
  nombre: z.string().min(1, 'Nombre requerido'),
  origen: z.string().min(1, 'Origen requerido'),
  destino: z.string().min(1, 'Destino requerido'),
})

export const rutasController = {
  async getAll(_req: Request, res: Response) {
    const rutas = await prisma.ruta.findMany({
      include: { _count: { select: { buses: true, viajes: true } } },
      orderBy: { createdAt: 'desc' },
    })
    return res.json({ data: rutas, total: rutas.length })
  },

  async getById(req: Request, res: Response) {
    const ruta = await prisma.ruta.findUnique({
      where: { id: req.params.id },
      include: {
        buses: true,
        viajes: {
          take: 20,
          orderBy: { fechaInicio: 'desc' },
          include: { bus: { select: { placa: true, nombre: true } } },
        },
      },
    })
    if (!ruta) return res.status(404).json({ error: 'Ruta no encontrada' })
    return res.json({ data: ruta })
  },

  async create(req: Request, res: Response) {
    const result = rutaSchema.safeParse(req.body)
    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    const ruta = await prisma.ruta.create({ data: result.data })
    return res.status(201).json({ data: ruta })
  },

  async update(req: Request, res: Response) {
    const result = rutaSchema.partial().safeParse(req.body)
    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    try {
      const ruta = await prisma.ruta.update({
        where: { id: req.params.id },
        data: result.data,
      })
      return res.json({ data: ruta })
    } catch {
      return res.status(404).json({ error: 'Ruta no encontrada' })
    }
  },
}