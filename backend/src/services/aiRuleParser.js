const { GoogleGenerativeAI } = require("@google/generative-ai");

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

async function parseEnglishToRules(userInput) {
  try {
    if (!userInput || typeof userInput !== "string") {
      throw new Error("Invalid query input");
    }

    const model = genAI.getGenerativeModel({
      model: "models/gemini-2.5-flash",
      generationConfig: {
        temperature: 0.1
      },
    });

    const prompt = `
You are a financial stock screener rule compiler.

Return ONLY valid JSON.

Schema:

{
  "filters": [
    { "field": "pe_ratio", "operator": "<", "value": 20 }
  ],
  "sector": null,
  "sort": {
    "field": "market_cap",
    "direction": "DESC"
  },
  "limit": null
}

Allowed fields:
current_price
market_cap
pe_ratio
peg_ratio
debt_to_fcf
revenue_growth
ebitda_growth
volume

Allowed operators:
>
<
>=
<=
=
between

Rules:
- If user says "top N", set limit = N.
- If user says "highest", sort DESC.
- If user says "lowest", sort ASC.
- If nothing specified, set null.
- No explanations.
- No markdown.
- JSON only.

User Query:
"${userInput}"
`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    const cleaned = text.replace(/```json|```/g, "").trim();

    let parsed;
    try {
      parsed = JSON.parse(cleaned);
    } catch (err) {
      console.error("Raw AI Output:", cleaned);
      throw new Error("AI returned invalid JSON");
    }

    // Safety defaults
    parsed.filters = parsed.filters || [];
    parsed.sort = parsed.sort || null;
    parsed.limit = parsed.limit || null;
    parsed.sector = parsed.sector || null;

    return parsed;

  } catch (error) {
    console.error("AI Rule Parser Error:", error.message);
    throw new Error("Failed to parse rule using AI");
  }
}

module.exports = {
  parseEnglishToRules,
};