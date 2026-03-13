function generateExplanation(dsl) {
  let explanation = "Screening stocks";

  if (dsl.filters.length) {
    explanation += " where ";

    const parts = dsl.filters.map(f => {
      if (f.operator === "between") {
        return `${f.field} between ${f.value[0]} and ${f.value[1]}`;
      }
      return `${f.field} ${f.operator} ${f.value}`;
    });

    explanation += parts.join(" AND ");
  }

  if (dsl.sort) {
    explanation += ` sorted by ${dsl.sort.field} (${dsl.sort.direction})`;
  }

  if (dsl.limit) {
    explanation += ` limited to top ${dsl.limit} results`;
  }

  return explanation;
}

module.exports = generateExplanation;