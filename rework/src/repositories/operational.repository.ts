import { prisma } from "../lib/prisma.js";
import { Contract } from "../modules/validators/waltz.ops.validators.js";
import { ContractIdentityPayload } from "../modules/validators/operations.validators.js";
import { error } from '../util/chalk_colors.js';
import { AuthContract, RegistrationContract } from "../modules/validators/waltz.contract.validator.js";

export async function getSecret(id: string) {
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

type ClientContractResult<T> =
    | { success: true; details: T; callback_url: string }
    | { success: false; details: string };

export function getClientContract(id: ContractIdentityPayload, reqType: "auth"): Promise<ClientContractResult<AuthContract>>;
export function getClientContract(id: ContractIdentityPayload, reqType: "register"): Promise<ClientContractResult<RegistrationContract>>;
export async function getClientContract(
    id: ContractIdentityPayload,
    reqType: "auth" | "register"
): Promise<ClientContractResult<AuthContract | RegistrationContract>> {
    const contracts = await prisma.contracts.findMany({
        where: {
            client_id: id.clientId
        }
    })

    const selectedContract = contracts.length === 1
        ? contracts[0]
        : contracts.find((contract) => contract.id === id.contractId)

    if (!selectedContract) {
        error("The contract ID is incorrect and does not correspond to any existing contract.")
        return {
            success: false,
            details: "The contract ID is incorrect and does not correspond to any existing contract."
        }
    }

    const masterContract = selectedContract.contract as Contract

    if (reqType === "auth") {
        return {
            success: true,
            details: masterContract.auth,
            callback_url: selectedContract.callback_url
        }
    }
    return {
        success: true,
        details: masterContract.registration,
        callback_url: selectedContract.callback_url
    }
}