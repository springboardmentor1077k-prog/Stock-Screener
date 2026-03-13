const express = require("express");
const router = express.Router();
const { getStockAdvisory } = require("../controllers/advisoryController");

router.get("/:symbol", getStockAdvisory);

module.exports = router;