const pool = require("../db/db");
const compileQuery = require("./queryCompiler");

async function evaluateAlerts() {
  try {
    const alertsRes = await pool.query(
      `SELECT * FROM alerts WHERE is_active = true`
    );

    for (const alert of alertsRes.rows) {
      const { id, name, dsl } = alert;

      if (!dsl) continue;

      const { query, values } = compileQuery(dsl);

      const result = await pool.query(query, values);

      if (result.rows.length > 0) {
        console.log(`🔔 Alert Triggered: ${name}`);
        console.log("Matching Stocks:", result.rows);

        await pool.query(
          `UPDATE alerts
           SET last_triggered_at = NOW()
           WHERE id = $1`,
          [id]
        );
      }
    }

  } catch (error) {
    console.error("Alert Engine Error:", error.message);
  }
}

module.exports = evaluateAlerts;