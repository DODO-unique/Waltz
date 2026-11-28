import { prisma } from '../../common/lib/prisma.js';
import { type ContractPacket } from '../validators/operation.validator.js';
import type { persistenceResult } from '../types/types.js';
import { done } from '../../common/util/logger.js';

export async function addContract(payload: ContractPacket) : Promise<persistenceResult> {
        console.dir(payload, { depth: null });
        console.log("Auth:", payload.contract?.auth);
        console.log("Registration:", payload.contract?.registration);
        const contract = await prisma.contracts.create({
        data: {
            contract: payload.contract,
            callback_url: payload.callback_url,
            clients: {
                connect: {
                    id: payload.clientId
                    }
                }
            }
        })

        done(contract)
    return {
        success: true,
        details: contract
    }
}