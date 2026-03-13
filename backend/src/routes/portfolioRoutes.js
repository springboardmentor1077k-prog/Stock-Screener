const authMiddleware = require("../middleware/authMiddleware");
const express = require("express");
const router = express.Router();

const {
  addToPortfolio,
  getPortfolio,
  deleteHolding
} = require("../controllers/portfolioController");

router.post("/", authMiddleware, addToPortfolio);
router.get("/", authMiddleware, getPortfolio);
router.delete("/:id", authMiddleware, deleteHolding);

module.exports = router;
