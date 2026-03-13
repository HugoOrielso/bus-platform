// src/routes/reportes.routes.ts
import { Router } from 'express'
import { reportesController } from '../controllers/reportes.controller'
import { authenticate } from '../middlewares/auth.middleware'

const reportesRouter = Router()

// reportesRouter.use(authenticate)

reportesRouter.get('/resumen',    reportesController.resumen)
reportesRouter.get('/buses',      reportesController.porBus)
reportesRouter.get('/viaje/:id',  reportesController.porViaje)

export default reportesRouter