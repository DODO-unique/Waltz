import { UUID } from "crypto";
import redis from "../../lib/redis.js";
import { transactionBody } from "../../types/rpc.types.js";

export type trasactionPayload = {
    tKey: UUID,
    tValue: transactionBody,
    expiry: number
}
export type testRedisPaylaod = {
    Id: UUID,
    value: string,
    expiry: number,
}

export async function createTransaction(payload: trasactionPayload) {
    const result = await redis.set(payload.tKey, JSON.stringify(payload.tValue), {
        EX: payload.expiry
    })
    return result
}

export async function claimAuthAttempt(transactionKey: string) {
    const attemptsKey = `${transactionKey}:auth-attempts`;
    const attempts = await redis.incr(attemptsKey);

    if (attempts === 1) {
        const transactionTtl = await redis.ttl(transactionKey);
        if (transactionTtl <= 0) {
            await redis.del(attemptsKey);
            return null;
        }
        await redis.expire(attemptsKey, transactionTtl);
    }

    return attempts;
}

export async function getTransaction(key: string) {
    const result = await redis.get(key);
    return result ? JSON.parse(result) : result
}

export async function checkTransaction(key: string) {
    return await redis.get(key)
}

export async function redisEntry(payload: testRedisPaylaod) {
    await redis.set(payload.Id, payload.value, {
        EX: payload.expiry
    })
}

export async function redisCheck(key: string) {
    return await redis.get(key) 
}