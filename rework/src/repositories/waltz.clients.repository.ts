import { prisma } from '../lib/prisma';
import {ContractSchema, CreateClient, CreateClientSchema, SecuritySchema} from '../modules/validators/waltz.ops.validators';
import { persistenceResult } from '../types/waltz.types';
import { error, success } from '../util/chalk_colors';
import { addSecurity } from './waltz.security.repository';
import { addContract } from './waltz.contract.respository';

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
        success(securityResult.details)
        const contractResult: persistenceResult = await addContract(ContractSchema.parse({
            clientId: client.id,
            contract: validatedPayload.contracts.contract
        }))
        success(contractResult.details)

        return {
            success: true,
            details: {
                clients: client,
                security: securityResult.details,
                contracts: contractResult.details
            }
        }

    }catch(err) {
        error(err)
        return {
            success: false,
            details: err
        }
    }

}