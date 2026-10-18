import { Router } from 'express';
import clientRoutes from './waltz.routes.js';
import rpcRoutes from './rcp.routes.js';

const router = Router();

router.use(clientRoutes);
router.use(rpcRoutes)

export default router;