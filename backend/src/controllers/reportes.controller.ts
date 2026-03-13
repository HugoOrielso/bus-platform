// src/controllers/reportes.controller.ts
import { Request, Response } from 'express'
import { prisma } from '../database/db.database'

export const reportesController = {
  async resumen(_req: Request, res: Response) {
    const hoy = new Date()
    hoy.setHours(0, 0, 0, 0)

    const [viajesHoy, totalPasajerosHoy, busesActivos, viajesEnCurso] = await Promise.all([
      prisma.viaje.count({ where: { fechaInicio: { gte: hoy } } }),
      prisma.conteo.count({ where: { timestamp: { gte: hoy }, tipo: 'SUBIDA' } }),
      prisma.bus.count({ where: { activo: true } }),
      prisma.viaje.count({ where: { estado: 'EN_CURSO' } }),
    ])

    const porHora = await prisma.$queryRaw<
      { hora: number; subidas: bigint; bajadas: bigint }[]
    >`
      SELECT
        EXTRACT(HOUR FROM timestamp)::int AS hora,
        COUNT(*) FILTER (WHERE tipo = 'SUBIDA') AS subidas,
        COUNT(*) FILTER (WHERE tipo = 'BAJADA') AS bajadas
      FROM conteos
      WHERE timestamp >= ${hoy}
      GROUP BY hora
      ORDER BY hora
    `

    return res.json({
      data: {
        resumen: { viajesHoy, totalPasajerosHoy, busesActivos, viajesEnCurso },
        pasajerosPorHora: porHora.map((r: { hora: any; subidas: any; bajadas: any }) => ({
          hora: r.hora,
          subidas: Number(r.subidas),
          bajadas: Number(r.bajadas),
        })),
      },
    })
  },

  async porBus(_req: Request, res: Response) {
    const hoy = new Date()
    hoy.setHours(0, 0, 0, 0)

    const buses = await prisma.bus.findMany({
      where: { activo: true },
      select: {
        id: true,
        placa: true,
        nombre: true,
        capacidad: true,
        ruta: { select: { nombre: true } },
        viajes: {
          where: { fechaInicio: { gte: hoy } },
          select: {
            id: true,
            totalSubidas: true,
            totalBajadas: true,
            pasajerosActual: true,
            estado: true,
            fechaInicio: true,
            fechaFin: true,
          },
        },
      },
    })

    const reporte = buses.map((bus: { viajes: any[] }) => ({
      ...bus,
      estadisticasHoy: {
        totalViajes: bus.viajes.length,
        totalPasajeros: bus.viajes.reduce((acc, v) => acc + v.totalSubidas, 0),
        pasajerosActual: bus.viajes.find((v) => v.estado === 'EN_CURSO')?.pasajerosActual ?? 0,
        viajeActivo: bus.viajes.find((v) => v.estado === 'EN_CURSO') ?? null,
      },
    }))

    return res.json({ data: reporte })
  },

  async porViaje(req: Request, res: Response) {
    const viaje = await prisma.viaje.findUnique({
      where: { id: req.params.id },
      include: {
        bus: { select: { placa: true, nombre: true, capacidad: true } },
        ruta: { select: { nombre: true, origen: true, destino: true } },
        conteos: { orderBy: { timestamp: 'asc' } },
      },
    })

    if (!viaje) return res.status(404).json({ error: 'Viaje no encontrado' })

    // Reconstruir evolución de pasajeros en el tiempo
    let pasajeros = 0
    const evolucion = viaje.conteos.map((c: { tipo: string; timestamp: any; fuente: any; confianza: any }) => {
      pasajeros = c.tipo === 'SUBIDA' ? pasajeros + 1 : Math.max(0, pasajeros - 1)
      return {
        timestamp: c.timestamp,
        tipo: c.tipo,
        pasajeros,
        fuente: c.fuente,
        confianza: c.confianza,
      }
    })

    const duracionMinutos = viaje.fechaFin
      ? Math.round((viaje.fechaFin.getTime() - viaje.fechaInicio.getTime()) / 60000)
      : null

    const ocupacionMaxima = evolucion.length > 0
      ? Math.max(...evolucion.map((e: { pasajeros: any }) => e.pasajeros))
      : 0

    const porcentajeOcupacion = viaje.totalSubidas > 0
      ? Math.round((ocupacionMaxima / viaje.bus.capacidad) * 100)
      : 0

    return res.json({
      data: {
        viaje: {
          ...viaje,
          duracionMinutos,
          ocupacionMaxima,
          porcentajeOcupacion,
        },
        evolucion,
      },
    })
  },
}