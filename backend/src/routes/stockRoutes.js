const express = require("express");
const router = express.Router();

const {
  getAllStocks,
  screenStocks,
  screenStocksAI,
  manualScreener
} = require("../controllers/stockController");

/* ==========================
   GET ALL STOCKS
   GET /api/stocks
========================== */
router.get("/", getAllStocks);

/* ==========================
   BASIC SCREENER
   GET /api/stocks/screener
========================== */
router.get("/screener", screenStocks);

/* ==========================
   MANUAL SCREENER
   POST /api/stocks/manual-screener
========================== */
router.post("/manual-screener", manualScreener);

/* ==========================
   AI SCREENER
   POST /api/stocks/ai-screener
========================== */
router.post("/ai-screener", screenStocksAI);

module.exports = router;