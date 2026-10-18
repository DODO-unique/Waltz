import Express, { Router } from 'express';
import { addClient } from "../../repositories/waltz.clients.repository.js";
import { error } from '../../util/chalk_colors.js';
import typeValidator from '../middleware/validation.middleware.js';
import { CreateClientSchema } from '../validators/waltz.ops.validators.js';

const route = Router()

route.get("/api", (req, res) => {
    res.send("Got you!")
})

route.post("/api/addUser", Express.json(), typeValidator(CreateClientSchema), async (req, res) => {

    const result = await addClient(req.body)

    if (!result.success) {
        error(result.details)
        return res.status(400).send(
            result.details
        )
    }
    
    return res.status(201).send({
        clientId: result.details.clients.id,
        clientSecret: result.details.security.client_secret
    })
}) 

export default route;   