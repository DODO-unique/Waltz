import { UUID } from "crypto";
import { prisma } from "../lib/prisma.js";
import { Contract, ContractPacket } from "../modules/validators/waltz.ops.validators.js";
import { ContractIdentityPayload } from "../modules/validators/operations.validators.js";
import { error } from '../util/chalk_colors.js';
import { persistenceResult } from "../types/waltz.types.js";

export async function getSecret(id: UUID) {
    const client = await prisma.security.findUnique({
        where: {
            client_id: id
        }
    })

    if (client) {
        return client.client_secret
    } 
    return client
}

export async function getClientContract(id: ContractIdentityPayload, reqType: "auth" | "register"): Promise<persistenceResult>  {
    const contracts = await prisma.contracts.findMany({
        where: {
            client_id: id.clientId
        }
    })

    const masterContract = (contracts.length === 1 
    ? contracts[0].contract
    : contracts.find(
        (contract) => {
            contract.id === id.contractId
        }
    ) ?.contract) as Contract

    if (typeof masterContract === "undefined") {
        error("The contract ID is incorrect and does not correspond to any existing contract.")
        return {
            success: false,
            details: "The contract ID is incorrect and does not correspond to any existing contract."
        }
    }

    
    if (reqType === "auth") {
        return {
            success: true,
            details: masterContract.auth
        }
    }
    return {
        success: true,
        details: masterContract.registration
    }


}