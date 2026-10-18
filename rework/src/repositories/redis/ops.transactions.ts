import { UUID } from "crypto";
import redis from "../../lib/redis.js";

export type trasactionPayload = {
    trasactionId: UUID,
    transactionURL: string,
    expiry: number,
}
export type testRedisPaylaod = {
    Id: UUID,
    value: string,
    expiry: number,
}

export async function createTransaction(payload: trasactionPayload) {
    await redis.set(payload.trasactionId, payload.transactionURL, {
        EX: payload.expiry
    })
}

export async function redisEntry(payload: testRedisPaylaod) {
    await redis.set(payload.Id, payload.value, {
        EX: payload.expiry
    })
}

export async function redisCheck(key: string) {
    return await redis.get(key) 
}