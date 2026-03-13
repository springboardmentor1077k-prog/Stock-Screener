const express = require("express");
const router = express.Router();

const {
  getWatchlist,
  addToWatchlist
} = require("../controllers/watchlistController");

// GET WATCHLIST
router.get("/", getWatchlist);

// ADD STOCK
router.post("/", addToWatchlist);

module.exports = router;