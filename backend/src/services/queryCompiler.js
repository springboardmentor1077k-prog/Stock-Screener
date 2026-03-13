const allowedSortFields = [
  "current_price",
  "market_cap",
  "pe_ratio",
  "peg_ratio",
  "debt_to_fcf",
  "revenue_growth",
  "ebitda_growth",
  "volume"
];

const compileQuery = (dsl) => {
  let query = `
    SELECT 
      symbol,
      company_name,
      sector,
      current_price,
      pe_ratio,
      peg_ratio,
      market_cap,
      revenue_growth,
      ebitda_growth,
      debt_to_fcf,
      volume
    FROM stocks
    WHERE 1=1
  `;

  const values = [];
  let index = 1;

  // 🔹 Filters
  if (dsl.filters) {
    for (const filter of dsl.filters) {
      if (filter.operator === "between") {
        query += ` AND ${filter.field} BETWEEN $${index} AND $${index + 1}`;
        values.push(filter.value[0], filter.value[1]);
        index += 2;
      } else {
        query += ` AND ${filter.field} ${filter.operator} $${index}`;
        values.push(filter.value);
        index++;
      }
    }
  }

  // 🔹 Sector filter
  if (dsl.sector) {
    query += ` AND sector = $${index}`;
    values.push(dsl.sector);
    index++;
  }

  // 🔹 Sorting
  if (dsl.sort && allowedSortFields.includes(dsl.sort.field)) {
    query += ` ORDER BY ${dsl.sort.field} ${dsl.sort.direction}`;
  }

  // 🔹 Limit
  if (dsl.limit) {
    query += ` LIMIT ${dsl.limit}`;
  }

  return { query, values };
};

module.exports = compileQuery;