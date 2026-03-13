// src/app/dashboard/_hooks/useDashboard.ts
'use client'

import { api } from '@/lib/api'
import { wsClient } from '@/lib/ws'
import { useEffect, useState, useCallback } from 'react'


export function useDashboard() {
  const [resumen, setResumen]       = useState<ResumenData | null>(null)
  const [buses, setBuses]           = useState<BusReporte[]>([])
  const [viajes, setViajes]         = useState<Viaje[]>([])
  const [loading, setLoading]       = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const precio = 3000

  const fetchAll = useCallback(async () => {
    try {
      const [resumenRes, busesRes, viajesRes] = await Promise.all([
        api.get<{ data: ResumenData }>('/reportes/resumen'),
        api.get<{ data: BusReporte[] }>('/reportes/buses'),
        api.get<{ data: Viaje[] }>('/viajes?limite=20'),
      ])
      setResumen(resumenRes.data)
      setBuses(busesRes.data)
      setViajes(viajesRes.data)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Error fetching dashboard:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Actualizar un viaje en estado local sin refetch completo
  const patchViaje = useCallback((viajeId: string, patch: Partial<Viaje>) => {
    setViajes((prev) =>
      prev.map((v) => (v.id === viajeId ? { ...v, ...patch } : v))
    )
    setBuses((prev) =>
      prev.map((b) => ({
        ...b,
        estadisticasHoy: b.estadisticasHoy.viajeActivo?.id === viajeId
          ? {
              ...b.estadisticasHoy,
              pasajerosActual: patch.pasajerosActual ?? b.estadisticasHoy.pasajerosActual,
              viajeActivo: b.estadisticasHoy.viajeActivo
                ? { ...b.estadisticasHoy.viajeActivo, ...patch }
                : null,
            }
          : b.estadisticasHoy,
      }))
    )
    setLastUpdate(new Date())
  }, [])

  useEffect(() => {
    fetchAll()

    // Conectar WS al canal del dashboard
    wsClient.connect('__dashboard__')

    const unsub = wsClient.on('*', (raw) => {
      const msg = raw as { type: string; payload: WsConteoEvent & WsViajeEvent['payload'] }

      if (msg.type === 'CONTEO') {
        const p = msg.payload as WsConteoEvent
        patchViaje(p.viajeId, {
          pasajerosActual: p.pasajerosActual,
          totalSubidas: p.totalSubidas,
          totalBajadas: p.totalBajadas,
        })
        // Actualizar resumen en vivo
        setResumen((prev) => {
          if (!prev || p.tipo !== 'SUBIDA') return prev
          return {
            ...prev,
            resumen: {
              ...prev.resumen,
              totalPasajerosHoy: prev.resumen.totalPasajerosHoy + 1,
            },
          }
        })
      }

      if (msg.type === 'VIAJE_UPDATE') {
        // Refetch completo cuando cambia la lista de viajes
        fetchAll()
      }
    })

    return () => {
      unsub()
      wsClient.disconnect()
    }
  }, [fetchAll, patchViaje])

  const recaudacionTotal = viajes
    .filter((v) => v.estado !== 'CANCELADO')
    .reduce((acc, v) => acc + v.totalSubidas * precio, 0)

  const recaudacionPorViaje = (v: Viaje) => v.totalSubidas * precio

  return {
    resumen,
    buses,
    viajes,
    loading,
    lastUpdate,
    recaudacionTotal,
    recaudacionPorViaje,
    precio,
    refetch: fetchAll,
  }
}