import { Router } from 'express';
import clientRoutes from './waltz.routes.js';
import rpcRoutes from './rcp.routes.js';
import webRoutes from './web.routes.js';

const router = Router();

router.use(clientRoutes);
router.use(rpcRoutes);
router.use(webRoutes)

export default router;