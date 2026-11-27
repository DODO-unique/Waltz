import Express from "express";
import core from "./core/cr.index.js";
import client from "./client/lnt.index.js";


const app = Express();

app.use(Express.json());

// mount the client
app.use("/client", client);
// mount the core
app.use("/core", core);


const PORT = 3000;

app.listen(PORT, () => {
    console.log(`You are connected to port ${PORT}! Connect to backend: http://localhost:3000/`)
}) 


app.get("/test", (req, res) => {
    console.log("Hey!")
    return res.send( {
        "Are you connected?" : "Yes",
        "Is this a good example" : "No"
    });
})