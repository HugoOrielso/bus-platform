// src/app/dashboard/_components/PasajerosChart.tsx
'use client'

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

interface Props {
  data: PasajerosPorHora[]
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#0F1117', border: '1px solid #1F2937',
      borderRadius: '8px', padding: '10px 14px',
    }}>
      <p style={{ color: '#9CA3AF', margin: '0 0 6px', fontSize: '12px' }}>{`${label}:00 hs`}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color, margin: '2px 0', fontSize: '13px' }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  )
}

export function PasajerosChart({ data }: Props) {
  const filled = Array.from({ length: 24 }, (_, hora) => {
    const found = data.find((d) => d.hora === hora)
    return { hora: String(hora).padStart(2, '0'), subidas: found?.subidas ?? 0, bajadas: found?.bajadas ?? 0 }
  })

  return (
    <div style={{
      background: '#0F1117', border: '1px solid #1F2937',
      borderRadius: '12px', padding: '24px',
    }}>
      <p style={{ color: '#F9FAFB', fontWeight: 600, margin: '0 0 20px', fontFamily: '"DM Mono", monospace' }}>
        Pasajeros por hora
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={filled} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
          <XAxis dataKey="hora" tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#4B5563', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1F293740' }} />
          <Legend wrapperStyle={{ fontSize: '12px', color: '#6B7280' }} />
          <Bar dataKey="subidas" fill="#00E5A0" radius={[3, 3, 0, 0]} maxBarSize={20} />
          <Bar dataKey="bajadas" fill="#F87171" radius={[3, 3, 0, 0]} maxBarSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}