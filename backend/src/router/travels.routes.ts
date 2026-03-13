// src/routes/viajes.routes.ts
import { Router } from 'express'
import { viajesController } from '../controllers/viajes.controller'
import { authenticate, authorize } from '../middlewares/auth.middleware'

const viajesRouter = Router()

// viajesRouter.use(authenticate)

viajesRouter.get('/',        viajesController.getAll)
viajesRouter.get('/activos', viajesController.getActivos)
viajesRouter.get('/:id',     viajesController.getById)

viajesRouter.post('/iniciar',      authorize('ADMIN', 'SUPERVISOR', 'OPERADOR'), viajesController.iniciar)
viajesRouter.post('/:id/conteo',   viajesController.registrarConteo)
viajesRouter.patch('/:id/finalizar', authorize('ADMIN', 'SUPERVISOR', 'OPERADOR'), viajesController.finalizar)

export default viajesRouter