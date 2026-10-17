import Express, { Router } from 'express';
import { addClient } from "../../repositories/waltz.clients.repository";
import { error } from '../../util/chalk_colors';
import { typeValidator } from '../middleware/validation.middleware';
import { CreateClientSchema } from '../validators/waltz.ops.validators';

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
    
    return res.status(201).send("Success!")
}) 

export default route;   