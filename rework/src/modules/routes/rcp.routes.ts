import { Router } from "express";
import typeValidator from "../middleware/validation.middleware";
import { operationalRequestSchema, operationalRequestType } from "../validators/operations.validators";
import { autethenticator } from "../middleware/authention.middleware";
import { error, success } from "../../util/chalk_colors";
import { getClientContract } from "../../repositories/operational.repository";
import { genAuthSchema } from "../validators/ops.generate.validator";


const route = Router();

route.get("/status", (req, res) => {
    return res.status(200).send("Service is available.")
})

route.post("/request", autethenticator(), async (req, res) => {
    const reqBody = operationalRequestSchema.safeParse(req.body)

    if (!reqBody.success) {
        error(reqBody.error)
        return res.status(400).send("Payload format is incorrect")
    } 
    success(reqBody.data)

    if (reqBody.data.reqType === "auth") {
        const contract = await getClientContract(reqBody.data.ID, "auth")
        if (!contract.success) {
            res.status(400).send(contract.details)
        }
        const contractSchema = genAuthSchema(contract.details)
        const parsedContract = contractSchema.safeParse(reqBody.data)
        // we parsed up a auth contract. We would now setup a redis contract
    }
})

export default route;