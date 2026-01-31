const pool = require("../db/db");

/**
 * 1️⃣ Fetch all stocks
 * GET /api/stocks
 */
const getAllStocks = async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM stocks");
    res.status(200).json(result.rows);
  } catch (error) {
    console.error("Error fetching stocks:", error);
    res.status(500).json({ message: "Server error" });
  }
};

/**
 * 2️⃣ Screen stocks dynamically
 * GET /api/stocks/screener
 */
const screenStocks = async (req, res) => {
  try {
    const {
      maxPE,
      maxPEG,
      maxDebtToFCF,
      revenueGrowth,
      ebitdaGrowth,
    } = req.query;

    // Base query
    let query = "SELECT * FROM stocks WHERE 1=1";
    let values = [];

    // ❌ Exclude consulting companies (business logic)
    query += `
      AND company_name NOT ILIKE '%Consultancy%'
      AND company_name NOT ILIKE '%Services%'
    `;

    // 🔍 Apply filters dynamically
    if (maxPE) {
      values.push(maxPE);
      query += ` AND pe_ratio <= $${values.length}`;
    }

    if (maxPEG) {
      values.push(maxPEG);
      query += ` AND peg_ratio <= $${values.length}`;
    }

    if (maxDebtToFCF) {
      values.push(maxDebtToFCF);
      query += ` AND debt_to_fcf <= $${values.length}`;
    }

    if (revenueGrowth !== undefined) {
      values.push(revenueGrowth === "true");
      query += ` AND revenue_growth = $${values.length}`;
    }

    if (ebitdaGrowth !== undefined) {
      values.push(ebitdaGrowth === "true");
      query += ` AND ebitda_growth = $${values.length}`;
    }

    const result = await pool.query(query, values);
    res.status(200).json(result.rows);
  } catch (error) {
    console.error("Error screening stocks:", error);
    res.status(500).json({ message: "Server error" });
  }
};
const buildStockQuery = require("../services/queryBuilder");

const screenStocksAI = async (req, res) => {
  try {
    // TEMP: manual rules (AI comes next)
    const rules = req.body;

    const { query, values } = buildStockQuery(rules);
    const result = await pool.query(query, values);

    res.status(200).json(result.rows);
  } catch (error) {
    console.error("AI Screener Error:", error);
    res.status(500).json({ message: "Server error" });
  }
};


module.exports = {
  getAllStocks,
  screenStocks,
  screenStocksAI,
};
