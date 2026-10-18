import { RequestHandler } from "express";
import jwt from "jsonwebtoken";
import { getSecret } from "../../repositories/operational.repository.js";
import { error } from "../../util/chalk_colors.js";

export const autethenticator = (): RequestHandler => {
    // This funciton verifies the jwt token and adds the jwt payload to request body.
    // Note that the request body is not validated.

    return async (req, res, next) => {
        if (typeof req.headers.authorization === "undefined") {
            return res.status(400).send("Waltz Authenticator middleware: No authorization header found.")
        }
        const token = req.headers.authorization?.split(" ")[1]

        const { clientId } = req.body

        if (typeof clientId === "undefined") {
            error("No clientId provided or incorrect field name given in the post body")
            error("Aborting with 404 ...")
            return res.status(400).send("No clientID provided in the post body.")
        }

        const secret: null | string = await getSecret(clientId)

        if (!secret) {
            error("Client not found. Sending 404 and aborting...")
            return res.status(404).send("Client not found.")
        }
        try {
            let payload = jwt.verify(token, secret, { algorithms: ['HS256']})
            if (typeof payload === "string") payload = JSON.parse(payload)
            req.body = payload;
            next();
        } catch (err) {
            error("An error occured while trying to verify token using secret: ", err)
            error("Aborting with Unauthorized...")
            return res.send(401).send("Client HMAC verification failed")
        }
    }
}