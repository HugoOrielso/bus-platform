// src/controllers/viajes.controller.ts
import { Request, Response } from 'express'
import { z } from 'zod'
import { AuthRequest } from '../types'
import { prisma } from '../database/db.database'
import { wsService } from '../services/websocket/websocket.service'

const iniciarSchema = z.object({
  busId: z.string().uuid('UUID de bus inválido'),
  rutaId: z.string().uuid('UUID de ruta inválido'),
})

const conteoSchema = z.object({
  tipo: z.enum(['SUBIDA', 'BAJADA']),
  fuente: z.enum(['CAMARA', 'KINECT', 'MANUAL']).default('MANUAL'),
  confianza: z.number().min(0).max(1).optional(),
})

const filtrosSchema = z.object({
  estado: z.enum(['EN_CURSO', 'FINALIZADO', 'CANCELADO']).optional(),
  busId: z.string().uuid().optional(),
  limite: z.string().regex(/^\d+$/).optional(),
})

export const viajesController = {
  async getAll(req: AuthRequest, res: Response) {
    const result = filtrosSchema.safeParse(req.query)
    if (!result.success) {
      return res.status(400).json({ error: 'Filtros inválidos' })
    }

    const { estado, busId, limite = '50' } = result.data

    const viajes = await prisma.viaje.findMany({
      where: {
        ...(estado && { estado }),
        ...(busId && { busId }),
      },
      include: {
        bus: { select: { placa: true, nombre: true, capacidad: true } },
        ruta: { select: { nombre: true, origen: true, destino: true } },
        _count: { select: { conteos: true } },
      },
      orderBy: { fechaInicio: 'desc' },
      take: parseInt(limite),
    })

    return res.json({ data: viajes, total: viajes.length })
  },

  async getActivos(_req: Request, res: Response) {
    const viajes = await prisma.viaje.findMany({
      where: { estado: 'EN_CURSO' },
      include: {
        bus: { select: { placa: true, nombre: true, capacidad: true } },
        ruta: { select: { nombre: true, origen: true, destino: true } },
      },
      orderBy: { fechaInicio: 'desc' },
    })
    return res.json({ data: viajes, total: viajes.length })
  },

  async getById(req: Request, res: Response) {
    const viaje = await prisma.viaje.findUnique({
      where: { id: req.params.id },
      include: {
        bus: true,
        ruta: true,
        conteos: { orderBy: { timestamp: 'desc' }, take: 100 },
      },
    })
    if (!viaje) return res.status(404).json({ error: 'Viaje no encontrado' })
    return res.json({ data: viaje })
  },

  async iniciar(req: AuthRequest, res: Response) {
    const result = iniciarSchema.safeParse(req.body)
    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    const { busId, rutaId } = result.data

    // Verificar que el bus existe y está activo
    const bus = await prisma.bus.findUnique({ where: { id: busId } })
    if (!bus) return res.status(404).json({ error: 'Bus no encontrado' })
    if (!bus.activo) return res.status(409).json({ error: 'El bus está desactivado' })

    // Verificar que la ruta existe
    const ruta = await prisma.ruta.findUnique({ where: { id: rutaId } })
    if (!ruta) return res.status(404).json({ error: 'Ruta no encontrada' })

    // Verificar que el bus no tenga viaje activo
    const viajeActivo = await prisma.viaje.findFirst({
      where: { busId, estado: 'EN_CURSO' },
    })
    if (viajeActivo) {
      return res.status(409).json({
        error: 'El bus ya tiene un viaje en curso',
        viajeId: viajeActivo.id,
      })
    }

    const viaje = await prisma.viaje.create({
      data: { busId, rutaId },
      include: {
        bus: { select: { placa: true, nombre: true, capacidad: true } },
        ruta: { select: { nombre: true, origen: true, destino: true } },
      },
    })

    // Notificar al dashboard global que hay un nuevo viaje
    wsService.emit('__dashboard__', {
      type: 'VIAJE_UPDATE',
      payload: { accion: 'INICIADO', viaje },
    })

    return res.status(201).json({ data: viaje })
  },

  // ⭐ Endpoint principal — llamado por el servicio de visión (cámara/Kinect)
  async registrarConteo(req: AuthRequest, res: Response) {
    const result = conteoSchema.safeParse(req.body)
    if (!result.success) {
      return res.status(400).json({
        error: 'Datos inválidos',
        detalles: result.error.flatten().fieldErrors,
      })
    }

    const viaje = await prisma.viaje.findUnique({ where: { id: req.params.id } })
    if (!viaje) return res.status(404).json({ error: 'Viaje no encontrado' })
    if (viaje.estado !== 'EN_CURSO') {
      return res.status(409).json({ error: 'El viaje no está en curso' })
    }

    const { tipo, fuente, confianza } = result.data

    // Calcular nuevos pasajeros (nunca negativo, máximo 9999)
    const nuevosPasajeros =
      tipo === 'SUBIDA'
        ? Math.min(viaje.pasajerosActual + 1, 9999)
        : Math.max(viaje.pasajerosActual - 1, 0)

    // Transacción atómica: crear conteo + actualizar totales del viaje
    const [conteo, viajeActualizado] = await prisma.$transaction([
      prisma.conteo.create({
        data: { viajeId: viaje.id, tipo, fuente, confianza },
      }),
      prisma.viaje.update({
        where: { id: viaje.id },
        data: {
          pasajerosActual: nuevosPasajeros,
          ...(tipo === 'SUBIDA'
            ? { totalSubidas: { increment: 1 } }
            : { totalBajadas: { increment: 1 } }),
        },
      }),
    ])

    // Emitir evento en tiempo real al viaje y al dashboard
    wsService.emitConteo({
      viajeId: viaje.id,
      busId: viaje.busId,
      tipo,
      pasajerosActual: nuevosPasajeros,
      totalSubidas: viajeActualizado.totalSubidas,
      totalBajadas: viajeActualizado.totalBajadas,
      timestamp: conteo.timestamp.toISOString(),
      fuente,
      confianza,
    })

    return res.status(201).json({
      data: {
        conteo,
        pasajerosActual: nuevosPasajeros,
        totalSubidas: viajeActualizado.totalSubidas,
        totalBajadas: viajeActualizado.totalBajadas,
      },
    })
  },

  async finalizar(req: Request, res: Response) {
    try {
      const viaje = await prisma.viaje.findUnique({ where: { id: req.params.id } })
      if (!viaje) return res.status(404).json({ error: 'Viaje no encontrado' })
      if (viaje.estado !== 'EN_CURSO') {
        return res.status(409).json({ error: 'El viaje no está en curso' })
      }

      const viajeActualizado = await prisma.viaje.update({
        where: { id: req.params.id },
        data: { estado: 'FINALIZADO', fechaFin: new Date() },
        include: {
          bus: { select: { placa: true, nombre: true } },
          ruta: { select: { nombre: true } },
        },
      })

      // Notificar cierre del viaje
      wsService.emit(viaje.id, {
        type: 'VIAJE_UPDATE',
        payload: { accion: 'FINALIZADO', viajeId: viaje.id },
      })
      wsService.emit('__dashboard__', {
        type: 'VIAJE_UPDATE',
        payload: { accion: 'FINALIZADO', viaje: viajeActualizado },
      })

      return res.json({ data: viajeActualizado })
    } catch {
      return res.status(404).json({ error: 'Viaje no encontrado' })
    }
  },
}