// src/routes/reportes.routes.ts
import { Router } from 'express'
import { reportesController } from '../controllers/reportes.controller'
import { authenticate } from '../middlewares/auth.middleware'

const rutasRouter = Router()

rutasRouter.use(authenticate)

rutasRouter.get('/resumen',    reportesController.resumen)
rutasRouter.get('/buses',      reportesController.porBus)
rutasRouter.get('/viaje/:id',  reportesController.porViaje)

export default rutasRouter