import { Router } from "express";
import { checkTransaction, getTransaction } from "../../repositories/redis/ops.transactions.js";
import { error } from "../../util/chalk_colors.js";
import { transactionBody } from "../../types/rpc.types.js";
import fs from "node:fs";
import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";
import { getSecret } from "../../repositories/operational.repository.js";
import { claimAuthAttempt } from "../../repositories/redis/ops.transactions.js";
import { AuthRequestDataSchema, AuthSubmissionSchema, formSubmission, formSubmissionSchema, RegistrationSubmissionSchema } from "../validators/web.validation.js";
import typeValidator from "../middleware/validation.middleware.js";

const route = Router();

route.get("/waltz/health", (_, res) => {
    return res.status(200).send("Endpoint working!")
})

route.get("/waltz/:id", async (req, res) => {
    const tKey = req.params.id

    const tValue = await checkTransaction(tKey)

    if (!tValue) {
        error("No such key. Aborting...")
        return res.status(404).send("No such user")
    }

    let html = fs.readFileSync("./public/form.html", "utf-8")
    html = html.replace("__TRANSACTION_ID__", tKey)

    return res.type("html").send(html)
})

route.get("/waltz/:id/form.js", async (req, res) => {
    const tValue = await checkTransaction(req.params.id)

    if (!tValue) {
        error("No such key. Aborting...")
        return res.status(404).send("No such user")
    }

    const parsedTransactionValue: transactionBody = JSON.parse(tValue)

    const contract = Buffer.from(JSON.stringify(parsedTransactionValue.contract), "utf8").toString("base64url")
    const rtype = Buffer.from(JSON.stringify(parsedTransactionValue.rtype), "utf8").toString("base64url")
    const schema = Buffer.from(JSON.stringify(parsedTransactionValue.schema), "utf8").toString("base64url")

    let script = fs.readFileSync("./public/form.js", "utf-8")

    script = script.replace("__EXPRESS_FROM_TRANSACTION_ID_STRING_V1", req.params.id)
    script = script.replace("__EXPRESS_FORM_CONTRACT_B64URL_V1__", contract);
    script = script.replace("__EXPRESS_FORM_CONTRACT_TYPE_B64URL_V1__", rtype);
    script = script.replace("__EXPRESS_FORM_SCHEMA_B64URL_V1__", schema);

    return res.type("application/javascript").send(script);
})

route.post("/waltz/submit", typeValidator(formSubmissionSchema), async (req, res) => {
    const validatedPayload: formSubmission = req.body

    const tValue: null | transactionBody = await getTransaction(validatedPayload.tkey)

    if (!tValue) {
        error("The value is null. Expired or old key value. Aborting with 404...")
        return res.status(404).send("Key not found")
    }

    if (tValue.rtype === "auth") {
        const submission = AuthSubmissionSchema.safeParse(validatedPayload.body)
        if (!submission.success) {
            error("An error occurred while parsing authentication submission:", submission.error)
            return res.status(400).send(submission.error)
        }

        const authReqData = AuthRequestDataSchema.safeParse(tValue.authReqData)
        if (!authReqData.success || !tValue.clientId) {
            error("Authentication transaction is missing valid request data or client identity:", authReqData.success ? "clientId missing" : authReqData.error)
            return res.status(500).send("Authentication transaction is incorrectly configured")
        }

        const attempt = await claimAuthAttempt(validatedPayload.tkey)
        if (attempt === null) {
            return res.status(404).send("Authentication transaction expired")
        }
        if (attempt > 3) {
            return res.status(429).send({
                message: "Authentication attempt limit reached",
                attemptsRemaining: 0
            })
        }

        const { email, username } = submission.data.identifier
        const identifiersMatch =
            (email === undefined || authReqData.data.identifier.email === email)
            && (username === undefined || authReqData.data.identifier.username === username)

        let passwordMatches: boolean
        try {
            const submittedPasswordHash = await bcrypt.hash(
                submission.data.password,
                authReqData.data.password.salt
            )
            passwordMatches = submittedPasswordHash === authReqData.data.password.hash
        } catch (hashError) {
            error("Could not verify authentication password hash:", hashError)
            return res.status(500).send("Authentication could not be completed")
        }

        if (!identifiersMatch || !passwordMatches) {
            const attemptsRemaining = Math.max(0, 3 - attempt)
            error("Authentication failed", { attemptsRemaining })
            return res.status(401).send({
                message: attemptsRemaining
                    ? "Invalid credentials"
                    : "Invalid credentials; authentication attempt limit reached",
                attemptsRemaining
            })
        }

        const clientSecret = await getSecret(tValue.clientId)
        if (!clientSecret) {
            error("No client secret found for authentication transaction", tValue.clientId)
            return res.status(500).send("Authentication could not be completed")
        }

        const token = jwt.sign(
            { identifier: submission.data.identifier },
            clientSecret,
            { algorithm: "HS256", expiresIn: "5m" }
        )

        try {
            const callbackResponse = await fetch(`${tValue.callback_url.replace(/\/+$/, "")}/auth`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ token })
            })

            if (!callbackResponse.ok) {
                error("Authentication callback returned an unsuccessful response:", callbackResponse.status)
                return res.status(502).send("Authentication callback failed")
            }
        } catch (callbackError) {
            error("Could not send authentication token to callback:", callbackError)
            return res.status(502).send("Could not reach authentication callback")
        }

        return res.status(200).send({ message: "Authenticated successfully" })
    }

    if (tValue.rtype === "register") {
        const submission = RegistrationSubmissionSchema.safeParse(validatedPayload.body)
        if (!submission.success) {
            error("An error occurred while parsing registration submission:", submission.error)
            return res.status(400).send(submission.error)
        }

        try {
            const callbackResponse = await fetch(`${tValue.callback_url}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(submission.data)
            })

            if (!callbackResponse.ok) {
                error("Registration callback returned an unsuccessful response:", callbackResponse.status)
                return res.status(502).send("Registration callback failed")
            }
        } catch (callbackError) {
            error("Could not send registration submission to callback:", callbackError)
            return res.status(502).send("Could not reach registration callback")
        }

        return res.status(200).send({ message: "Registration submitted successfully" })
    }
})

export default route;