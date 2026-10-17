import {prisma} from '../lib/prisma';
import { ContractPacket } from '../modules/validators/waltz.ops.validators';
import { persistenceResult } from '../types/waltz.types';
import { success, error } from '../util/chalk_colors';

export async function addContract(payload: ContractPacket) : Promise<persistenceResult> {
        console.dir(payload, { depth: null });
        console.log("Auth:", payload.contract?.auth);
        console.log("Registration:", payload.contract?.registration);
        const contract = await prisma.contracts.create({
        data: {
            contract: payload.contract,
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