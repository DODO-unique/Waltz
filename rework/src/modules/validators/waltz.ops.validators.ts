import { z } from 'zod';
import { AuthContractSchema, RegistrationContractSchema } from './waltz.contract.validator.js';

export const ContractSchema = z.object({
  clientId: z.uuid(),
  contract: z.object({
    auth: AuthContractSchema,
    registration: RegistrationContractSchema,
  })
});

export type ContractPacket = z.infer<typeof ContractSchema>;

export const SecuritySchema = z.object({
    clientId: z.uuid(),
    clientSecret: z.uuid(),
    passwordHash: z.string()
});

export type Security = z.infer<typeof SecuritySchema>

export const CreateClientSchema = z.object({
    name: z.string().max(400),
    email: z.email(),
    contracts: ContractSchema.omit({clientId: true}),
    security: SecuritySchema.omit({clientId: true})
})

export type CreateClient = z.infer<typeof CreateClientSchema>