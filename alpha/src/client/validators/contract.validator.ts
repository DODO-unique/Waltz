import { email, z } from 'zod';

export const ContractFieldDefinitions = {
    username: z.string().min(3),
    email: z.email(),
    fullname: z.string(),
    age: z.number().int().positive(),
    address: z.string(),
    password: z.string().min(8),
}

export const AuthIdentifierSchema = z
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
    )

export type AuthIdentifier = z.infer<typeof AuthIdentifierSchema>

export const AuthContractSchema = z.object({
  identifier: AuthIdentifierSchema,
  password: z.boolean().default(false),
});

export type AuthContract = z.infer<typeof AuthContractSchema>

export const RegistrationContractSchema = z.object({
  username: z.boolean().default(false),
  fullname: z.boolean().default(false),
  age: z.boolean().default(false),
  address: z.boolean().default(false),
  password: z.boolean().default(false),
});

export type RegistrationContract = z.infer<typeof RegistrationContractSchema>

