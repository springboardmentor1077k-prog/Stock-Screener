const axios = require("axios");
const pool = require("../db/db");

const API_KEY = process.env.FMP_API_KEY;

const STOCK_SYMBOLS = [
  "AAPL",
  "MSFT",
  "GOOGL",
  "AMZN",
  "META",
  "NVDA",
  "TSLA",
  "IBM",
  "ORCL",
  "INTC"
];

async function fetchAndStoreStocks() {
  try {
    console.log("Fetching stock data from FMP (stable API)...");

    for (let symbol of STOCK_SYMBOLS) {
      try {
        // Run both API calls in parallel
        const [quoteRes, metricsRes] = await Promise.all([
          axios.get(
            `https://financialmodelingprep.com/stable/quote?symbol=${symbol}&apikey=${API_KEY}`
          ),
          axios.get(
            `https://financialmodelingprep.com/stable/key-metrics?symbol=${symbol}&apikey=${API_KEY}`
          )
        ]);

        const stock = quoteRes.data?.[0];
        const metrics = metricsRes.data?.[0];

        if (!stock) {
          console.log(`No data for ${symbol}`);
          continue;
        }

        const earningsYield = metrics?.earningsYield;
        const calculatedPE = earningsYield ? Number((1 / earningsYield).toFixed(2)) : null;


        await pool.query(
          `
          INSERT INTO stocks
          (symbol, company_name, current_price, market_cap, pe_ratio, updated_at)
          VALUES ($1,$2,$3,$4,$5,NOW())
          ON CONFLICT (symbol)
          DO UPDATE SET
            current_price = EXCLUDED.current_price,
            market_cap = EXCLUDED.market_cap,
            pe_ratio = EXCLUDED.pe_ratio,
            updated_at = NOW();
          `,
          [
            stock.symbol,
            stock.name,
            stock.price,
            stock.marketCap,
            calculatedPE
          ]
        );

        console.log(`Updated: ${symbol}`);
      } catch (err) {
        console.log(`Skipped ${symbol}: ${err.message}`);
      }
    }

    console.log("Stock data update completed.");
  } catch (error) {
    console.error("Stock Data Error:", error.message);
  }
}

module.exports = { fetchAndStoreStocks };
