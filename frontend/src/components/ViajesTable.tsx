// src/app/dashboard/_components/ViajesTable.tsx
'use client'


interface Props {
  viajes: Viaje[]
  recaudacionPorViaje: (v: Viaje) => number
}

const fmt = (n: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n)

const fmtHora = (iso: string) =>
  new Date(iso).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })

const estadoBadge: Record<string, { label: string; color: string; bg: string }> = {
  EN_CURSO:   { label: 'En curso',   color: '#00E5A0', bg: '#00E5A011' },
  FINALIZADO: { label: 'Finalizado', color: '#6B7280', bg: '#6B728011' },
  CANCELADO:  { label: 'Cancelado',  color: '#F87171', bg: '#F8717111' },
}

export function ViajesTable({ viajes, recaudacionPorViaje }: Props) {
  return (
    <div style={{
      background: '#0F1117', border: '1px solid #1F2937',
      borderRadius: '12px', overflow: 'hidden',
    }}>
      <div style={{ padding: '20px 24px', borderBottom: '1px solid #1F2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <p style={{ color: '#F9FAFB', fontWeight: 600, margin: 0, fontFamily: '"DM Mono", monospace' }}>
          Viajes del día
        </p>
        <span style={{ color: '#4B5563', fontSize: '12px' }}>{viajes.length} viajes</span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0A0D14' }}>
              {['Bus', 'Ruta', 'Inicio', 'Pasajeros', '↑ Sub', '↓ Baj', 'Recaudación', 'Estado'].map((h) => (
                <th key={h} style={{
                  padding: '10px 16px', textAlign: 'left',
                  color: '#4B5563', fontSize: '11px', fontWeight: 500,
                  letterSpacing: '0.08em', textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {viajes.length === 0 && (
              <tr>
                <td colSpan={8} style={{ padding: '40px', textAlign: 'center', color: '#4B5563', fontSize: '14px' }}>
                  No hay viajes registrados hoy
                </td>
              </tr>
            )}
            {viajes.map((v, i) => {
              const badge = estadoBadge[v.estado] ?? estadoBadge.CANCELADO
              const isLive = v.estado === 'EN_CURSO'
              return (
                <tr key={v.id} style={{
                  borderTop: '1px solid #1F2937',
                  background: i % 2 === 0 ? 'transparent' : '#0A0D1440',
                  transition: 'background 0.15s',
                }}>
                  <td style={{ padding: '14px 16px', whiteSpace: 'nowrap' }}>
                    <span style={{ color: '#F9FAFB', fontWeight: 600, fontFamily: 'monospace' }}>{v.bus.placa}</span>
                    <br />
                    <span style={{ color: '#6B7280', fontSize: '11px' }}>{v.bus.nombre}</span>
                  </td>
                  <td style={{ padding: '14px 16px', color: '#9CA3AF', fontSize: '13px', whiteSpace: 'nowrap' }}>
                    {v.ruta.origen} → {v.ruta.destino}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#6B7280', fontSize: '13px', fontFamily: 'monospace' }}>
                    {fmtHora(v.fechaInicio)}
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'center' }}>
                    <span style={{
                      color: isLive ? '#00E5A0' : '#9CA3AF',
                      fontWeight: 700, fontSize: '18px', fontFamily: '"DM Mono", monospace',
                    }}>
                      {isLive && <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#00E5A0', marginRight: 6, animation: 'pulse 1.5s infinite' }} />}
                      {v.pasajerosActual}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', color: '#00E5A0', textAlign: 'center', fontFamily: 'monospace' }}>{v.totalSubidas}</td>
                  <td style={{ padding: '14px 16px', color: '#F87171', textAlign: 'center', fontFamily: 'monospace' }}>{v.totalBajadas}</td>
                  <td style={{ padding: '14px 16px', color: '#A855F7', fontFamily: '"DM Mono", monospace', whiteSpace: 'nowrap' }}>
                    {fmt(recaudacionPorViaje(v))}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      background: badge.bg, color: badge.color,
                      border: `1px solid ${badge.color}44`,
                      borderRadius: '20px', padding: '3px 10px', fontSize: '11px', fontWeight: 500,
                    }}>
                      {badge.label}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}