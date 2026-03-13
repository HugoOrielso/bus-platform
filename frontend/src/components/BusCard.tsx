// src/app/dashboard/_components/BusCard.tsx
'use client'


interface Props {
  bus: BusReporte
}

export function BusCard({ bus }: Props) {
  const { estadisticasHoy: stats } = bus
  const isLive = !!stats.viajeActivo
  const pct = Math.min(100, Math.round((stats.pasajerosActual / bus.capacidad) * 100))

  const barColor =
    pct >= 90 ? '#F87171' :
    pct >= 70 ? '#F59E0B' :
    '#00E5A0'

  return (
    <div style={{
      background: '#0F1117',
      border: `1px solid ${isLive ? '#00E5A033' : '#1F2937'}`,
      borderRadius: '12px',
      padding: '20px',
      position: 'relative',
    }}>
      {isLive && (
        <span style={{
          position: 'absolute', top: 14, right: 14,
          background: '#00E5A011', color: '#00E5A0',
          border: '1px solid #00E5A033', borderRadius: '20px',
          padding: '2px 8px', fontSize: '11px', fontWeight: 600,
        }}>● VIVO</span>
      )}

      <div style={{ marginBottom: 16 }}>
        <p style={{ color: '#F9FAFB', fontWeight: 700, margin: '0 0 2px', fontFamily: 'monospace', fontSize: '16px' }}>
          {bus.placa}
        </p>
        <p style={{ color: '#6B7280', fontSize: '12px', margin: 0 }}>
          {bus.ruta?.nombre ?? 'Sin ruta'} · cap. {bus.capacidad}
        </p>
      </div>

      {/* Barra de ocupación */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ color: '#6B7280', fontSize: '11px' }}>Ocupación</span>
          <span style={{ color: barColor, fontSize: '11px', fontFamily: 'monospace' }}>
            {stats.pasajerosActual}/{bus.capacidad} ({pct}%)
          </span>
        </div>
        <div style={{ background: '#1F2937', borderRadius: 4, height: 6 }}>
          <div style={{
            background: barColor, borderRadius: 4, height: 6,
            width: `${pct}%`, transition: 'width 0.4s ease',
          }} />
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
        {[
          { label: 'Viajes', value: stats.totalViajes },
          { label: '↑ Sub', value: stats.totalPasajeros, color: '#00E5A0' },
          { label: 'Pasaj.', value: stats.pasajerosActual, color: isLive ? '#3B82F6' : undefined },
        ].map((s) => (
          <div key={s.label} style={{
            background: '#0A0D14', borderRadius: 8, padding: '10px',
            textAlign: 'center',
          }}>
            <p style={{ color: s.color ?? '#9CA3AF', fontSize: '16px', fontWeight: 700, margin: '0 0 2px', fontFamily: 'monospace' }}>
              {s.value}
            </p>
            <p style={{ color: '#4B5563', fontSize: '10px', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {s.label}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}