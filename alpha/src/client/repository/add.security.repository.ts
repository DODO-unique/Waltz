import { prisma } from '../../common/lib/prisma.js';
import { type Security } from '../validators/operation.validator.js';
import type { persistenceResult } from '../types/types.js';
import { done } from '../../common/util/logger.js';

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

        done(security)
    return {
        success: true,
        details: security
    }
}