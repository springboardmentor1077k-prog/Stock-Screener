const express = require("express");
const router = express.Router();

const { getAllStocks } = require("../controllers/stockController");

// GET /api/stocks
router.get("/", getAllStocks);

module.exports = router;
