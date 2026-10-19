import {prisma} from '../lib/prisma.js';
import { ContractPacket } from '../modules/validators/waltz.ops.validators.js';
import { persistenceResult } from '../types/waltz.types.js';
import { success } from '../util/chalk_colors.js';

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

        success(contract)
    return {
        success: true,
        details: contract
    }
}