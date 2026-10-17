import { z } from 'zod';
const AuthContractSchema = z.object({
  identifier: z
    .object({
      email: z.boolean().default(false),
      username: z.boolean().default(false),
    })
    .refine(
      (identifiers) =>
        identifiers.email || identifiers.username,
      {
        message:
          "At least one of email or username must be enabled",
      },
    ),
  password: z.boolean().default(false),
});

const RegistrationContractSchema = z.object({
  username: z.boolean().default(false),
  fullname: z.boolean().default(false),
  age: z.boolean().default(false),
  address: z.boolean().default(false),
  password: z.boolean().default(false),
});

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