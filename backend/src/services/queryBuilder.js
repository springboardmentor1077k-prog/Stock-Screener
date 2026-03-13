/**
 * Builds safe SQL query from AI-generated rule JSON
 * Fully parameterized to prevent SQL injection
 */

const buildStockQuery = (rules) => {
  let baseQuery = `
    SELECT 
      symbol,
      company_name,
      ROUND(current_price::numeric, 2) AS current_price,
      ROUND(pe_ratio::numeric, 2) AS pe_ratio,
      ROUND(market_cap::numeric, 0) AS market_cap
    FROM stocks
    WHERE 1=1
  `;

  const values = [];
  let paramIndex = 1;

  // ✅ Handle Conditions
  if (rules.conditions && Array.isArray(rules.conditions)) {
    for (const condition of rules.conditions) {

      const allowedFields = ["current_price", "market_cap", "pe_ratio", "volume"];
      const allowedOperators = [">", "<", ">=", "<=", "=", "between"];

      if (
        !allowedFields.includes(condition.field) ||
        !allowedOperators.includes(condition.operator)
      ) {
        continue; // Skip invalid condition
      }

      if (condition.operator === "between" && Array.isArray(condition.value)) {
        baseQuery += ` AND ${condition.field} BETWEEN $${paramIndex} AND $${paramIndex + 1}`;
        values.push(condition.value[0], condition.value[1]);
        paramIndex += 2;
      } else {
        baseQuery += ` AND ${condition.field} ${condition.operator} $${paramIndex}`;
        values.push(condition.value);
        paramIndex++;
      }
    }
  }

  // ✅ Sorting
  if (rules.sort && rules.sort.field && rules.sort.direction) {
    const allowedSortFields = ["current_price", "market_cap", "pe_ratio", "volume"];
    const direction = rules.sort.direction.toUpperCase() === "DESC" ? "DESC" : "ASC";

    if (allowedSortFields.includes(rules.sort.field)) {
      baseQuery += ` ORDER BY ${rules.sort.field} ${direction}`;
    }
  }

  // ✅ Limit
  if (rules.limit && Number.isInteger(rules.limit)) {
    baseQuery += ` LIMIT ${rules.limit}`;
  }

  return {
    query: baseQuery,
    values
  };
};

module.exports = buildStockQuery;
