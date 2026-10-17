import { z } from 'zod';

export const operationalRequestSchema = z.object({
    clientId: z.uuidv4(),
    reqType: z.literal(["register", "auth"]),
    reqBody: z.object().optional()
})

export type operationalRequestType = z.infer<typeof operationalRequestSchema>