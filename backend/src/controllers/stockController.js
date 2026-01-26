const pool = require("../db/db");

const getAllStocks = async (req, res) => {
  try {
    const result = await pool.query("SELECT * FROM stocks");
    res.status(200).json(result.rows);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Server error" });
  }
};

module.exports = { getAllStocks };
