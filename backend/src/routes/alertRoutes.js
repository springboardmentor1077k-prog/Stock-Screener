const express = require("express");
const router = express.Router();
const pool = require("../db/db");
const authMiddleware = require("../middleware/authMiddleware");

/* ==========================
   GET USER ALERTS
========================== */
router.get("/", authMiddleware, async (req, res, next) => {
  try {
    const userId = req.user.id || req.user.userId;

    const result = await pool.query(
      `SELECT * FROM alerts 
       WHERE user_id = $1 
       ORDER BY created_at DESC`,
      [userId]
    );

    res.json({
      success: true,
      alerts: result.rows,
    });

  } catch (error) {
    next(error);
  }
});

/* ==========================
   CREATE ALERT
========================== */
router.post("/", authMiddleware, async (req, res, next) => {
  try {
    const { name, dsl } = req.body;
    const userId = req.user.id || req.user.userId;

    const result = await pool.query(
      `INSERT INTO alerts (user_id, name, dsl)
       VALUES ($1, $2, $3)
       RETURNING *`,
      [userId, name, JSON.stringify(dsl)]
    );

    res.status(201).json({
      success: true,
      alert: result.rows[0],
    });

  } catch (error) {
    next(error);
  }
});

module.exports = router;