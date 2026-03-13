// src/app/dashboard/page.tsx
'use client'

import { StatsCards } from "@/components/StatsCards"
import { useDashboard } from "./hooks/useDashboard"
import { PasajerosChart } from "@/components/PasajerosChart"
import { BusCard } from "@/components/BusCard"
import { ViajesTable } from "@/components/ViajesTable"


export default function DashboardPage() {
  const {
    resumen, buses, viajes, loading,
    lastUpdate, recaudacionTotal,
    recaudacionPorViaje, refetch,
  } = useDashboard()

  return (
    <div style={{
      minHeight: '100vh',
      background: '#060810',
      color: '#F9FAFB',
      fontFamily: '"DM Sans", sans-serif',
      padding: '0',
    }}>
      {/* Importar fuentes */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500;600&display=swap');
        * { box-sizing: border-box; }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeIn 0.4s ease both; }
      `}</style>

      {/* Header */}
      <div style={{
        borderBottom: '1px solid #1F2937',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#0A0D14',
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 22 }}>🚌</span>
          <div>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, fontFamily: '"DM Mono", monospace', color: '#F9FAFB' }}>
              Bus Platform
            </h1>
            <p style={{ margin: 0, fontSize: 11, color: '#4B5563', letterSpacing: '0.08em' }}>
              DASHBOARD OPERACIONAL
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ color: '#4B5563', fontSize: 12, fontFamily: 'monospace' }}>
            Actualizado: {lastUpdate.toLocaleTimeString('es-CO')}
          </span>
          <button
            onClick={refetch}
            style={{
              background: 'transparent', border: '1px solid #374151',
              color: '#9CA3AF', padding: '6px 14px', borderRadius: 8,
              cursor: 'pointer', fontSize: 13,
            }}
          >
            ↺ Refrescar
          </button>
        </div>
      </div>

      <div style={{ padding: '28px 32px', maxWidth: 1400, margin: '0 auto' }}>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
            <div style={{ color: '#4B5563', fontFamily: 'monospace' }}>Cargando datos...</div>
          </div>
        ) : (
          <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

            {/* Stats cards */}
            {resumen && (
              <StatsCards
                stats={resumen.resumen}
                recaudacion={recaudacionTotal}
              />
            )}

            {/* Gráfica + Buses en vivo */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 20 }}>
              {resumen && <PasajerosChart data={resumen.pasajerosPorHora} />}

              {/* Panel buses */}
              <div style={{
                background: '#0F1117', border: '1px solid #1F2937',
                borderRadius: 12, padding: 20,
                display: 'flex', flexDirection: 'column', gap: 12,
              }}>
                <p style={{ color: '#F9FAFB', fontWeight: 600, margin: '0 0 4px', fontFamily: '"DM Mono", monospace' }}>
                  Buses activos
                </p>
                {buses.length === 0 && (
                  <p style={{ color: '#4B5563', fontSize: 13, textAlign: 'center', margin: 'auto' }}>
                    No hay buses activos
                  </p>
                )}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, overflowY: 'auto', maxHeight: 260 }}>
                  {buses.map((b) => <BusCard key={b.id} bus={b} />)}
                </div>
              </div>
            </div>

            {/* Tabla de viajes */}
            <ViajesTable
              viajes={viajes}
              recaudacionPorViaje={recaudacionPorViaje}
            />

          </div>
        )}
      </div>
    </div>
  )
}