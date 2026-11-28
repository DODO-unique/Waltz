import { prisma } from '../../common/lib/prisma.js';
import {ContractPacketSchema, type CreateClient, CreateClientSchema, SecuritySchema} from '../validators/operation.validator.js';
import type { persistenceResult } from '../types/types.js';
import { fail, done } from '../../common/util/logger.js';
import { addSecurity } from './add.security.repository.js';
import { addContract } from './add.contract.respository.js';

export async function addClient(payload: CreateClient) : Promise<persistenceResult> {
    // CHeck if payload is valid:
    const result = CreateClientSchema.safeParse(payload);

    if (!result.success) {
        return {
            success: false,
            details: result.error
        }
    }

    const validatedPayload = result.data

    try {
        const client = await prisma.clients.create({
            data: {
                name: validatedPayload.name,
                email: validatedPayload.email
            }
        })
        const securityResult: persistenceResult = await addSecurity(SecuritySchema.parse({
            clientId: client.id,
            clientSecret: validatedPayload.security.clientSecret,
            passwordHash: validatedPayload.security.passwordHash
        }))
        done(securityResult.details)
        const contractResult: persistenceResult = await addContract(ContractPacketSchema.parse({
            clientId: client.id,
            callback_url: validatedPayload.contracts.callback_url,
            contract: validatedPayload.contracts.contract
        }))
        done(contractResult.details)

        return {
            success: true,
            details: {
                clients: client,
                security: securityResult.details,
                contracts: contractResult.details
            }
        }

    }catch(err) {
        fail(err)
        return {
            success: false,
            details: err
        }
    }

}