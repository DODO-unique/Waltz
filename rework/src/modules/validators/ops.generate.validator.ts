import { z } from "zod";
import {
  AuthContract,
  ContractFieldDefinitions,
  type RegistrationContract,
  AuthIdentifier,
} from "./waltz.contract.validator.js";

export const PasswordOpSchema = z.object({
  hash: z.string(),
  salt: z.string(),
});

export type PasswordOp = z.infer<typeof PasswordOpSchema>;

export function genRegistrationSchema(contract: RegistrationContract) {
  let shape: Record<string, z.ZodType> = {};

  for (const key of Object.keys(contract) as (keyof RegistrationContract)[]) {
    if (key === "password") {
      shape[key] = contract[key] ? PasswordOpSchema : PasswordOpSchema.optional();
      continue;
    }
    const fieldSchema = ContractFieldDefinitions[key];
    shape[key] = contract[key] ? fieldSchema : fieldSchema.optional();
  }
  return z.object(shape);
}

export function genAuthSchema(contract: AuthContract | AuthIdentifier) {
  let shape: Record<string, z.ZodType> = {};

  for (const key of Object.keys(contract) as (keyof AuthContract)[]) {
    const value = contract[key as keyof typeof contract];

    if (typeof value !== "boolean") {
      const childShape = genAuthSchema(value);
      shape[key] = childShape;
      continue;
    }

    if (key === "password") {
      shape[key] = value ? PasswordOpSchema : PasswordOpSchema.optional();
      continue;
    }

    const fieldSchema =
      ContractFieldDefinitions[key as keyof typeof ContractFieldDefinitions];

    shape[key] = value ? fieldSchema : fieldSchema.optional();
  }

  return z.object(shape);
}
