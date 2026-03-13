const pool = require("../db/db");
const { GoogleGenerativeAI } = require("@google/generative-ai");

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

async function generateStockAdvisory(symbol) {
  try {
    // 1️⃣ Fetch stock data
    const result = await pool.query(
      `SELECT * FROM stocks WHERE symbol = $1`,
      [symbol]
    );

    if (result.rows.length === 0) {
      throw new Error("Stock not found");
    }

    const stock = result.rows[0];

    // 2️⃣ Basic Quantitative Scoring Model (Professional touch)
    let score = 0;

    if (stock.pe_ratio > 0 && stock.pe_ratio < 20) score += 2;
    if (stock.peg_ratio && stock.peg_ratio < 1.5) score += 2;
    if (stock.debt_to_fcf !== null && stock.debt_to_fcf < 1) score += 2;
    if (stock.revenue_growth) score += 2;
    if (stock.ebitda_growth) score += 2;

    let riskLevel = "Medium";
    if (stock.debt_to_fcf > 2) riskLevel = "High";
    if (score >= 7) riskLevel = "Low";

    // 3️⃣ Prepare AI Prompt with Financial Context
    const model = genAI.getGenerativeModel({
      model: "models/gemini-2.5-flash",
      generationConfig: { temperature: 0.4 }
    });

    const prompt = `
You are a professional equity research analyst.

Analyze the following stock fundamentals and generate structured advisory.

Stock Data:
Symbol: ${stock.symbol}
Company: ${stock.company_name}
Sector: ${stock.sector}
Current Price: ${stock.current_price}
PE Ratio: ${stock.pe_ratio}
PEG Ratio: ${stock.peg_ratio}
Market Cap: ${stock.market_cap}
Revenue Growth: ${stock.revenue_growth}
EBITDA Growth: ${stock.ebitda_growth}
Debt to FCF: ${stock.debt_to_fcf}

Return ONLY JSON in this format:

{
  "summary": "Short 3-4 sentence professional summary",
  "strengths": ["point1", "point2"],
  "risks": ["risk1", "risk2"],
  "recommendation": "BUY | HOLD | SELL",
  "confidence": 75
}

Rules:
- Confidence must be 0-100 number
- No markdown
- No explanation outside JSON
`;

    const response = await model.generateContent(prompt);
    const text = response.response.text();
    const cleaned = text.replace(/```json|```/g, "").trim();

    const aiResult = JSON.parse(cleaned);

    // 4️⃣ Combine Quant + AI
    return {
      symbol: stock.symbol,
      company: stock.company_name,
      quantitativeScore: score,
      riskLevel,
      aiAdvisory: aiResult
    };

  } catch (error) {
    console.error("Advisory Engine Error:", error.message);
    throw new Error("Failed to generate advisory");
  }
}

module.exports = { generateStockAdvisory };