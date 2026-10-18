import { z } from 'zod';

export const ContractIdentityPayloadSchema = z.object({
        contractId: z.uuid().optional(),
        clientId: z.uuid()
    })

export type ContractIdentityPayload = z.infer<typeof ContractIdentityPayloadSchema>

export const operationalRequestSchema = z.object({
    ID: ContractIdentityPayloadSchema,
    reqType: z.literal(["register", "auth"]),
    reqBody: z.record(z.string(), z.unknown())
})

export type operationalRequestType = z.infer<typeof operationalRequestSchema>