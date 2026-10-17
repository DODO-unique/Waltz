import { Router } from 'express';
import clientRoutes from './waltz.routes';

const router = Router();

router.use(clientRoutes);

export default router;