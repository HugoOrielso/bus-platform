// src/types/dashboard.ts

 type EstadoViaje = 'EN_CURSO' | 'FINALIZADO' | 'CANCELADO'
 type TipoConteo = 'SUBIDA' | 'BAJADA'
 type FuenteConteo = 'CAMARA' | 'KINECT' | 'MANUAL'

 interface Ruta {
  nombre: string
  origen: string
  destino: string
}

 interface Bus {
  placa: string
  nombre: string
  capacidad: number
}

 interface Viaje {
  id: string
  estado: EstadoViaje
  fechaInicio: string
  fechaFin: string | null
  totalSubidas: number
  totalBajadas: number
  pasajerosActual: number
  bus: Bus
  ruta: Ruta
  _count?: { conteos: number }
}

 interface ResumenStats {
  viajesHoy: number
  totalPasajerosHoy: number
  busesActivos: number
  viajesEnCurso: number
}

 interface PasajerosPorHora {
  hora: number
  subidas: number
  bajadas: number
}

 interface ResumenData {
  resumen: ResumenStats
  pasajerosPorHora: PasajerosPorHora[]
}

 interface BusReporte {
  id: string
  placa: string
  nombre: string
  capacidad: number
  ruta: { nombre: string } | null
  viajes: Viaje[]
  estadisticasHoy: {
    totalViajes: number
    totalPasajeros: number
    pasajerosActual: number
    viajeActivo: Viaje | null
  }
}

// Evento WebSocket del backend
 interface WsConteoEvent {
  viajeId: string
  busId: string
  tipo: TipoConteo
  pasajerosActual: number
  totalSubidas: number
  totalBajadas: number
  timestamp: string
  fuente: FuenteConteo
  confianza: number | null
}

 interface WsViajeEvent {
  type: 'VIAJE_UPDATE'
  payload: {
    accion: 'INICIADO' | 'FINALIZADO'
    viaje?: Viaje
    viajeId?: string
  }
}

 type WsMessage =
  | { type: 'CONTEO'; payload: WsConteoEvent }
  | WsViajeEvent

// Precio por defecto hasta que se defina en DB
 const PRECIO_PASAJE_DEFAULT = 2500