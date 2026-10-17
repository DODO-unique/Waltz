import type { Request, Response, NextFunction } from "express";

export type middlewareArgs = {
    req: Request, 
    res: Response, 
    next: NextFunction
}