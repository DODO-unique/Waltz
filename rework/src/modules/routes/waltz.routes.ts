import { typeValidator } from "../middleware/validation.middleware";
import Express, { Router } from 'express';
import { operationalRequestSchema } from "../validators/operations.validators";
import { error, success } from "../../util/chalk_colors";
import { addClient } from "../../repositories/waltz.clients.repository";

const route = Router()

route.get("/api", (req, res) => {
    res.send("Got you!")
})

route.post("/api/addUser", Express.json(), async (req, res) => {

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