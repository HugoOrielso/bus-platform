import { Request, Response } from 'express'
import { z } from 'zod'
import { prisma } from '../database/db.database'

type BusParams = {
  id: string
}

const busSchema = z.object({
  placa: z.string().min(1, 'Placa requerida'),
  nombre: z.string().min(1, 'Nombre requerido'),
  capacidad: z.number().int().positive('Capacidad debe ser positiva'),
  rutaId: z.string().uuid('UUID de ruta inválido').optional(),
})

export const busesController = {
  async getAll(_req: Request, res: Response) {
    const buses = await prisma.bus.findMany({
      include: {
        ruta: true,
        viajes: {
          where: { estado: 'EN_CURSO' },
          take: 1,
          orderBy: { fechaInicio: 'desc' },
        },
      },
      orderBy: { createdAt: 'desc' },
    })

    return res.json({ data: buses, total: buses.length })
  },

  async getById(req: Request<BusParams>, res: Response) {
    const bus = await prisma.bus.findUnique({
      where: { id: req.params.id },
      include: {
        ruta: true,
        viajes: {
          take: 10,
          orderBy: { fechaInicio: 'desc' },
          include: {
            _count: {
              select: { conteos: true },
            },
          },
        },
      },
    })

    if (!bus) {
      return res.status(404).json({ error: 'Bus no encontrado' })
    }

    return res.json({ data: bus })
  },

  async create(req: Request, res: Response) {
    const result = busSchema.safeParse(req.body)

    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    const bus = await prisma.bus.create({
      data: result.data,
      include: { ruta: true },
    })

    return res.status(201).json({ data: bus })
  },

  async update(req: Request<BusParams>, res: Response) {
    const result = busSchema.partial().safeParse(req.body)

    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    try {
      const bus = await prisma.bus.update({
        where: { id: req.params.id },
        data: result.data,
        include: { ruta: true },
      })

      return res.json({ data: bus })
    } catch {
      return res.status(404).json({ error: 'Bus no encontrado' })
    }
  },

  async deactivate(req: Request<BusParams>, res: Response) {
    try {
      await prisma.bus.update({
        where: { id: req.params.id },
        data: { activo: false },
      })

      return res.json({ message: 'Bus desactivado correctamente' })
    } catch {
      return res.status(404).json({ error: 'Bus no encontrado' })
    }
  },
}