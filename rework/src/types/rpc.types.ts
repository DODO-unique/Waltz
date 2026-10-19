import { AuthContract, AuthContractSchema, RegistrationContract, RegistrationContractSchema } from "../modules/validators/waltz.contract.validator.js"
import { z } from "zod";

export const transactionBodySchema = z.object({
  rtype: z.enum(["auth", "register"]),
  contract: z.union([AuthContractSchema, RegistrationContractSchema]),
  schema: z.record(z.string(), z.custom<z.ZodType>()),
  callback_url: z.string(),
  clientId: z.uuid().optional(),
  authReqData: z.record(z.string(), z.unknown()).optional(),
});

export type transactionBody = z.infer<typeof transactionBodySchema>