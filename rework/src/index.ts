import Express from 'express';
import route from './modules/routes/routes';
import {log} from './util/chalk_colors';

const app = Express();

const PORT = 3000;

app.listen(PORT, () => {
    log(`You are connected to http://localhost:${PORT}`)
})

app.use(route)