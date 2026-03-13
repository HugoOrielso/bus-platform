// prisma/seed.ts
import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcrypt'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Seeding database...')

  // Usuarios
  const adminPassword = await bcrypt.hash('Admin123!', 10)
  const operadorPassword = await bcrypt.hash('Operador123!', 10)

  await prisma.user.upsert({
    where: { email: 'admin@busplatform.com' },
    update: {},
    create: {
      nombre: 'Administrador',
      email: 'admin@busplatform.com',
      password: adminPassword,
      rol: 'ADMIN',
    },
  })

  await prisma.user.upsert({
    where: { email: 'operador@busplatform.com' },
    update: {},
    create: {
      nombre: 'Operador Demo',
      email: 'operador@busplatform.com',
      password: operadorPassword,
      rol: 'OPERADOR',
    },
  })

  // Rutas
  const ruta1 = await prisma.ruta.upsert({
    where: { id: 'ruta-001' },
    update: {},
    create: { id: 'ruta-001', nombre: 'Ruta Centro - Norte', origen: 'Terminal Centro', destino: 'Terminal Norte' },
  })

  const ruta2 = await prisma.ruta.upsert({
    where: { id: 'ruta-002' },
    update: {},
    create: { id: 'ruta-002', nombre: 'Ruta Sur - Centro', origen: 'Terminal Sur', destino: 'Terminal Centro' },
  })

  // Buses
  await prisma.bus.upsert({
    where: { placa: 'ABC-123' },
    update: {},
    create: { id: 'bus-001', placa: 'ABC-123', nombre: 'Bus Azul 1', capacidad: 40, rutaId: ruta1.id },
  })

  await prisma.bus.upsert({
    where: { placa: 'XYZ-456' },
    update: {},
    create: { id: 'bus-002', placa: 'XYZ-456', nombre: 'Bus Rojo 2', capacidad: 35, rutaId: ruta2.id },
  })

  await prisma.bus.upsert({
    where: { placa: 'DEF-789' },
    update: {},
    create: { id: 'bus-003', placa: 'DEF-789', nombre: 'Bus Verde 3', capacidad: 45 },
  })

  console.log('✅ Seed completado!')
  console.log('👤 Admin:    admin@busplatform.com     / Admin123!')
  console.log('👤 Operador: operador@busplatform.com  / Operador123!')
}

main().catch(console.error).finally(() => prisma.$disconnect())