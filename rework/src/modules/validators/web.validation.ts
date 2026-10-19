import { z } from 'zod';

export const formSubmissionSchema = z.object({
    tkey: z.uuid(),
    body: z.record(z.string(), z.unknown())
})

export type formSubmission = z.infer<typeof formSubmissionSchema>

export const RegistrationSubmissionSchema = z.object({
    username: z.string().min(1).optional(),
    fullname: z.string().min(1).optional(),
    age: z.coerce.number().int().min(0).optional(),
    address: z.string().min(1).optional(),
    password: z.string().min(1).optional(),
});

export const AuthSubmissionSchema = z.object({
    identifier: z.object({
        email: z.string().email().optional(),
        username: z.string().min(1).optional(),
    }).refine(value => value.email || value.username),
    password: z.string().min(1),
});

export const AuthRequestDataSchema = z.object({
    identifier: z.object({
        email: z.string().email().optional(),
        username: z.string().min(1).optional(),
    }).refine(value => value.email || value.username),
    password: z.object({
        hash: z.string().min(1),
        salt: z.string().min(1),
    }),
});