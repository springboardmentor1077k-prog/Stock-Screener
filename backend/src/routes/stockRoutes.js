const express = require("express");
const router = express.Router();

const {
  getAllStocks,
  screenStocks,
  screenStocksAI,
} = require("../controllers/stockController");

// Normal APIs
router.get("/", getAllStocks);
router.get("/screener", screenStocks);

// AI-based screener
router.post("/ai-screener", screenStocksAI);

module.exports = router;
