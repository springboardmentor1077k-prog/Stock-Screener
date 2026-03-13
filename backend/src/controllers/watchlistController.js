const pool = require("../db/db");

/* GET WATCHLIST */
const getWatchlist = async (req, res) => {
  try {

    const result = await pool.query(`
      SELECT s.symbol, s.company_name, s.current_price
      FROM watchlist w
      JOIN stocks s ON w.symbol = s.symbol
    `);

    res.json({
      success: true,
      data: result.rows
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Error fetching watchlist" });
  }
};

/* ADD TO WATCHLIST */
const addToWatchlist = async (req, res) => {
  try {

    const { symbol } = req.body;

    await pool.query(
      "INSERT INTO watchlist(symbol) VALUES($1)",
      [symbol]
    );

    res.json({ success: true });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: "Error adding stock" });
  }
};

module.exports = {
  getWatchlist,
  addToWatchlist
};