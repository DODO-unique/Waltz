import type { RequestHandler } from "express";
import { z } from 'zod';
import {fail} from '../util/logger.js';

const typeValidator = (schema: z.ZodType): RequestHandler => {
    return (req, res, next) => {
       const result = schema.safeParse(req.body)
       if (!result.success) {
            fail(result.error)
            return res.status(400).send("Waltz type validator middleware: Incorrect request format")
       }
       req.body = result.data
       next()
   }
}

export default typeValidator;       