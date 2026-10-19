import { z } from 'zod';
import { AuthContractSchema, RegistrationContractSchema } from './waltz.contract.validator.js';

export const ContractSchema = z.object({
    auth: AuthContractSchema,
    registration: RegistrationContractSchema,
  })

  export type Contract = z.infer<typeof ContractSchema>

export const ContractPacketSchema = z.object({
  id: z.uuid().optional(),
  callback_url: z.string(),
  clientId: z.uuid(),
  contract: ContractSchema
});

export type ContractPacket = z.infer<typeof ContractPacketSchema>;

export const SecuritySchema = z.object({
    clientId: z.uuid(),
    clientSecret: z.uuid(),
    passwordHash: z.string()
});

export type Security = z.infer<typeof SecuritySchema>

export const CreateClientSchema = z.object({
    name: z.string().max(400),
    email: z.email(),
    contracts: ContractPacketSchema.omit({clientId: true}),
    security: SecuritySchema.omit({clientId: true})
})

export type CreateClient = z.infer<typeof CreateClientSchema>