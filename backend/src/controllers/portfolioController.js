const pool = require("../db/db");

/* =========================================
   Add Stock to Portfolio (JWT Protected)
========================================= */
const addToPortfolio = async (req, res) => {
  try {
    const userId = req.user.id; // 🔐 From JWT middleware
    const { symbol, quantity, buy_price } = req.body;

    if (!symbol || !quantity || !buy_price) {
      return res.status(400).json({
        success: false,
        message: "Missing fields"
      });
    }

    await pool.query(
      `INSERT INTO portfolio (user_id, symbol, quantity, buy_price)
       VALUES ($1, $2, $3, $4)`,
      [userId, symbol.toUpperCase(), quantity, buy_price]
    );

    res.status(201).json({
      success: true,
      message: "Added to portfolio"
    });

  } catch (error) {
    console.error("Portfolio Add Error:", error.message);
    res.status(500).json({
      success: false,
      message: "Server error"
    });
  }
};


/* =========================================
   Get Portfolio (User Specific)
========================================= */
const getPortfolio = async (req, res) => {
  try {
    const userId = req.user.id; // 🔐 From JWT middleware

    const result = await pool.query(
      `
      SELECT 
        p.id,
        p.symbol,
        s.company_name,
        p.quantity,
        p.buy_price,
        s.current_price,
        (p.quantity * p.buy_price) AS invested_value,
        (p.quantity * s.current_price) AS current_value,
        ((p.quantity * s.current_price) - (p.quantity * p.buy_price)) AS profit_loss
      FROM portfolio p
      JOIN stocks s ON p.symbol = s.symbol
      WHERE p.user_id = $1
      ORDER BY p.created_at DESC
      `,
      [userId]
    );

    const totalInvested = result.rows.reduce(
      (sum, r) => sum + Number(r.invested_value),
      0
    );

    const totalCurrent = result.rows.reduce(
      (sum, r) => sum + Number(r.current_value),
      0
    );

    res.json({
      success: true,
      holdings: result.rows,
      summary: {
        totalInvested,
        totalCurrent,
        totalProfitLoss: totalCurrent - totalInvested
      }
    });

  } catch (error) {
    console.error("Portfolio Fetch Error:", error.message);
    res.status(500).json({
      success: false,
      message: "Server error"
    });
  }
};


/* =========================================
   Delete Holding (User Protected)
========================================= */
const deleteHolding = async (req, res) => {
  try {
    const userId = req.user.id; // 🔐 From JWT middleware
    const { id } = req.params;

    const result = await pool.query(
      `DELETE FROM portfolio
       WHERE id = $1 AND user_id = $2
       RETURNING *`,
      [id, userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: "Holding not found or unauthorized"
      });
    }

    res.json({
      success: true,
      message: "Deleted successfully"
    });

  } catch (error) {
    console.error("Portfolio Delete Error:", error.message);
    res.status(500).json({
      success: false,
      message: "Server error"
    });
  }
};

module.exports = {
  addToPortfolio,
  getPortfolio,
  deleteHolding
};