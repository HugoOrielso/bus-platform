// src/routes/auth.routes.ts
import { Router } from 'express'
import { authController } from '../controllers/auth.controller'
import { authenticate } from '../middlewares/auth.middleware'

const authRouter = Router()

authRouter.post('/register', authController.register)
authRouter.post('/login',    authController.login)
authRouter.post('/refresh',  authController.refresh)
authRouter.post('/logout',   authenticate, authController.logout)
authRouter.get('/me',        authenticate, authController.me)

export default authRouter