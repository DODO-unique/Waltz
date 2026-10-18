import {prisma} from '../lib/prisma.js';
import { type Security } from '../modules/validators/waltz.ops.validators.js';
import { persistenceResult } from '../types/waltz.types.js';
import { success } from '../util/chalk_colors.js';

export async function addSecurity(payload: Security) : Promise<persistenceResult> {
    
        const security = await prisma.security.create({
        data: {
            client_secret: payload.clientSecret,
            password_hash: payload.passwordHash,
            clients: {
                connect: {
                    id: payload.clientId
                    }
                }
            }
        })

        success(security)
    return {
        success: true,
        details: security
    }
}