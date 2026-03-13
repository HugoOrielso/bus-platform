// src/app/dashboard/_components/StatsCards.tsx
'use client'


interface Props {
  stats: ResumenStats
  recaudacion: number
}

const fmt = (n: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

export function StatsCards({ stats, recaudacion }: Props) {
  const cards = [
    {
      label: 'Viajes hoy',
      value: stats.viajesHoy,
      sub: `${stats.viajesEnCurso} en curso`,
      color: '#00E5A0',
      icon: '🚌',
    },
    {
      label: 'Pasajeros hoy',
      value: stats.totalPasajerosHoy.toLocaleString('es-CO'),
      sub: 'subidas registradas',
      color: '#3B82F6',
      icon: '👥',
    },
    {
      label: 'Buses activos',
      value: stats.busesActivos,
      sub: `${stats.viajesEnCurso} con viaje`,
      color: '#F59E0B',
      icon: '🟢',
    },
    {
      label: 'Recaudación estimada',
      value: fmt(recaudacion),
      sub: `@ $3.000 por pasajero`,
      color: '#A855F7',
      icon: '💰',
    },
  ]

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
      gap: '16px',
    }}>
      {cards.map((c) => (
        <div key={c.label} style={{
          background: '#0F1117',
          border: `1px solid ${c.color}22`,
          borderRadius: '12px',
          padding: '24px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Glow accent */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
            background: c.color,
          }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: '#6B7280', fontSize: '12px', fontFamily: 'monospace', letterSpacing: '0.1em', textTransform: 'uppercase', margin: 0 }}>
                {c.label}
              </p>
              <p style={{ color: '#F9FAFB', fontSize: '28px', fontWeight: 700, margin: '8px 0 4px', fontFamily: '"DM Mono", monospace' }}>
                {c.value}
              </p>
              <p style={{ color: c.color, fontSize: '12px', margin: 0 }}>{c.sub}</p>
            </div>
            <span style={{ fontSize: '28px', opacity: 0.6 }}>{c.icon}</span>
          </div>
        </div>
      ))}
    </div>
  )
}