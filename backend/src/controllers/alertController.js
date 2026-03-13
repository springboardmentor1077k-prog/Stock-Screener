const pool = require("../db/db");
const compileQuery = require("../services/queryCompiler");
const { dslSchema } = require("../services/dslSchema");
const { parseEnglishToRules } = require("../services/aiRuleParser");

/**
 * Create Alert
 * POST /api/alerts
 */
const createAlert = async (req, res) => {
  try {
    const { name, query } = req.body;

    if (!name || !query) {
      return res.status(400).json({
        success: false,
        message: "Name and query are required"
      });
    }

    // AI → DSL
    const dsl = await parseEnglishToRules(query);

    // Validate
    const validatedDSL = dslSchema.parse(dsl);

    const result = await pool.query(
      `INSERT INTO alerts (name, dsl)
       VALUES ($1, $2)
       RETURNING *`,
      [name, validatedDSL]
    );

    res.status(201).json({
      success: true,
      alert: result.rows[0]
    });

  } catch (error) {
    console.error("Create Alert Error:", error.message);
    res.status(400).json({
      success: false,
      message: error.message
    });
  }
};
const getAlerts = async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT * FROM alerts ORDER BY created_at DESC`
    );

    res.status(200).json({
      success: true,
      alerts: result.rows
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: "Failed to fetch alerts"
    });
  }
};

module.exports = {
  createAlert,
  getAlerts
};