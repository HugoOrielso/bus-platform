// src/routes/buses.routes.ts
import { Router } from 'express'
import { busesController } from '../controllers/buses.controller'
import { authenticate, authorize } from '../middlewares/auth.middleware'

const busesRouter = Router()

busesRouter.use(authenticate)

busesRouter.get('/',    busesController.getAll)
busesRouter.get('/:id', busesController.getById)
busesRouter.post('/',   authorize('ADMIN', 'SUPERVISOR'), busesController.create)
busesRouter.patch('/:id', authorize('ADMIN', 'SUPERVISOR'), busesController.update)
busesRouter.delete('/:id', authorize('ADMIN'), busesController.deactivate)

export default busesRouter