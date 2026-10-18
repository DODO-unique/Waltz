import { Router } from "express";
import typeValidator from "../middleware/validation.middleware.js";
import { operationalRequestSchema, operationalRequestType } from "../validators/operations.validators.js";
import { autethenticator } from "../middleware/authention.middleware.js";
import { error, success } from "../../util/chalk_colors.js";
import { getClientContract } from "../../repositories/operational.repository.js";
import { genAuthSchema } from "../validators/ops.generate.validator.js";
import { log } from "../../util/chalk_colors.js";
import { redisCheck, redisEntry } from "../../repositories/redis/ops.transactions.js";


const route = Router();

route.post("/redis/status", async (req, res) => {
    log("Creating a redis entry. Query status/check to if it exists")
    await redisEntry({
        Id: req.body.Id,
        value: req.body.value,
        expiry: req.body.expiry
    })
        res.status(201).send({ message: "Redis entry created" });
})

route.get("/redis/status/check", async (req, res) => {
    const result = await redisCheck(req.query.key as string)
    res.send(result)
})

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