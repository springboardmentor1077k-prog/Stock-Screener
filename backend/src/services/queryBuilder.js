/**
 * Builds safe SQL query from rule JSON
 * This prevents SQL injection
 */
const buildStockQuery = (rules) => {
  let query = "SELECT * FROM stocks WHERE 1=1";
  let values = [];

  // Exclude consulting companies
  query += `
    AND company_name NOT ILIKE '%Consultancy%'
    AND company_name NOT ILIKE '%Services%'
  `;

  if (rules.maxPE) {
    values.push(rules.maxPE);
    query += ` AND pe_ratio <= $${values.length}`;
  }

  if (rules.maxPEG) {
    values.push(rules.maxPEG);
    query += ` AND peg_ratio <= $${values.length}`;
  }

  if (rules.maxDebtToFCF) {
    values.push(rules.maxDebtToFCF);
    query += ` AND debt_to_fcf <= $${values.length}`;
  }

  if (rules.revenueGrowth !== undefined) {
    values.push(rules.revenueGrowth);
    query += ` AND revenue_growth = $${values.length}`;
  }

  if (rules.ebitdaGrowth !== undefined) {
    values.push(rules.ebitdaGrowth);
    query += ` AND ebitda_growth = $${values.length}`;
  }

  return { query, values };
};

module.exports = buildStockQuery;
