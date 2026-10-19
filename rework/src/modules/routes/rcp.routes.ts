import { Router } from "express";
import { operationalRequestSchema } from "../validators/operations.validators.js";
import { autethenticator } from "../middleware/authention.middleware.js";
import { log, error, success } from "../../util/chalk_colors.js";
import { getClientContract } from "../../repositories/operational.repository.js";
import { genAuthSchema, genRegistrationSchema } from "../validators/ops.generate.validator.js";
import { createTransaction, getTransaction, redisCheck, redisEntry } from "../../repositories/redis/ops.transactions.js";
import process from "node:process";
import { AuthContract } from "../validators/waltz.contract.validator.js";

const BASE_URL = process.env.BASE_URL;


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

route.get("/request/fetch", async (req, res) => {
    const result = await getTransaction(req.query.tkey as string)
    return res.send({
        Tkey : req.query.tkey,
        Tvalue: result
    })
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
            error("The error:", contract.details)
            return res.status(400).send(contract.details)
        }
        log(contract.details)
        const contractSchema = genAuthSchema(contract.details)
        const parsedContract = contractSchema.safeParse(reqBody.data.reqBody)
        if (!parsedContract.success) {
            error("An Error occured while parsing request body for contract schema. The error:", parsedContract.error)
            return res.status(400).send(parsedContract.error)
        }
        // we parsed up a auth contract. We must create configurations. These configurations would be stored in Redis schema

        // create a transaction
        const transactionId = crypto.randomUUID()
        const transactionURL = `https://${BASE_URL}/waltz/${transactionId}`
        
        const result = await createTransaction({
            tKey: transactionId,
            tValue: {
                rtype: "auth",
                contract: contract.details,
                schema: contractSchema.shape,
                callback_url: contract.callback_url,
                clientId: reqBody.data.ID.clientId,
                authReqData: parsedContract.data
            },
            expiry: 600 //10 minutes
        })

        if (result !== "OK") {
            error("Error Occured while creating transaction entry. Aborting... ")
            return res.status(400).send("Could not create redis entry")
        }

        return res.status(200).send({
            transactionId: transactionId,
            transactionURL: transactionURL
        })
    }

    const contract = await getClientContract(reqBody.data.ID, "register")
    if (!contract.success) {
        error("The error:", contract.details)
        return res.status(400).send(contract.details)
    }
    log(contract.details)
    const contractSchema = genRegistrationSchema(contract.details)
    const parsedContract = contractSchema.safeParse(reqBody.data.reqBody)
    if (!parsedContract.success) {
        error("An Error occured while parsing request body for contract schema. The error:", parsedContract.error)
        return res.status(400).send(parsedContract.error)
    }

    const transactionId = crypto.randomUUID()
    const transactionURL = `https://${BASE_URL}/waltz/${transactionId}`

    const result = await createTransaction({
        tKey: transactionId,
        tValue: {
            rtype: "register",
            contract: contract.details,
            schema: contractSchema.shape,
            callback_url: contract.callback_url
        },
        expiry: 600 //10 minutes
    })

    if (result !== "OK") {
        error("Error Occured while creating transaction entry. Aborting... ")
        return res.status(400).send("Could not create redis entry")
    }

    return res.status(200).send({
        transactionId: transactionId,
        transactionURL: transactionURL
    })
})

export default route;