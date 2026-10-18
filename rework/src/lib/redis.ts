import { createClient } from "redis";
import { error } from "../util/chalk_colors.js";

const redis = createClient({
    url: "redis://localhost:6379",
});

redis.on("error", (err) => {
    error("Redis Client Error:", err)
})

export default redis;