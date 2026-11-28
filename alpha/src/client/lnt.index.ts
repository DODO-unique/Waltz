import { Router } from "express";
import typeValidator from "../common/middleware/validation.middleware.js";
import { CreateClientSchema } from "./validators/operation.validator.js";
import { addClient } from "./repository/add.clients.repository.js";
import { fail } from "../common/util/logger.js";

const client = Router();

client.get("/health", (req, res) => {
    res.send("Got you!")
})

client.post("/add/client", typeValidator(CreateClientSchema), async (req, res) => {

    const result = await addClient(req.body)

    if (!result.success) {
        fail(result.details)
        return res.status(400).send(
            result.details
        )
    }
    
    return res.status(201).send({
        clientId: result.details.clients.id,
        clientSecret: result.details.security.client_secret
    })
}) 

export default client;