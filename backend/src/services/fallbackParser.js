function fallbackParser(input) {
  const text = input.toLowerCase();
  const numbers = text.match(/\d+/g)?.map(Number) || [];

  const dsl = { filters: [], sort: null, limit: null };

  if (text.includes("pe") && text.includes("more")) {
    dsl.filters.push({
      field: "pe_ratio",
      operator: ">",
      value: numbers[0] || 20
    });
  }

  if (text.includes("pe") && text.includes("less")) {
    dsl.filters.push({
      field: "pe_ratio",
      operator: "<",
      value: numbers[0] || 20
    });
  }

  if (text.includes("top")) {
    dsl.limit = numbers[0] || 5;
  }

  return dsl;
}

module.exports = fallbackParser;