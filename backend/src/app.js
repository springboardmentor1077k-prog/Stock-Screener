const express = require("express");
const cors = require("cors");

const stockRoutes = require("./routes/stockRoutes");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api/stocks", stockRoutes);

module.exports = app;
