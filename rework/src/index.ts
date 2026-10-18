import Express from 'express';
import route from './modules/routes/routes.js';
import {log} from './util/chalk_colors.js';
import redis from './lib/redis.js';

const app = Express();
app.use(Express.json())

await redis.connect();
log("Redis Connected!")

const PORT = 3000;

app.listen(PORT, () => {
    log(`You are connected to http://localhost:${PORT}`)
})

app.use(route)