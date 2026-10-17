import { typeValidator } from "../middleware/validation.middleware";
import Express, { Router } from 'express';
import { operationalRequestSchema } from "../validators/operations.validators";
import { success } from "../../util/chalk_colors";

const route = Router()

route.get("/api", (req, res) => {
    res.send("Got you!")
})

route.post("/api/addUser", Express.json(), typeValidator(operationalRequestSchema), (req, res) => {
    const {
        clientId,
        reqType,
        reqBody
    } = req.body

    success(clientId, reqType, reqBody)
    return res.status(200).send("Success!")
}) 

export default route;