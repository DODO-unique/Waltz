import { RequestHandler } from "express";
import { middlewareArgs } from "../../types/middleware.types";
import { z } from 'zod';
import {error} from '../../util/chalk_colors'

export const typeValidator = (schema: z.ZodType): RequestHandler => {
    return (req, res, next) => {
       const result = schema.safeParse(req.body)
       if (!result.success) {
            error(result.error)
           return res.status(400).send("Incorrect request format")
       }
       req.body = result.data
       next()
   }
}