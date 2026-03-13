require("dotenv").config();

const express = require("express");
const cors = require("cors");
const cron = require("node-cron");

/* ==========================
   ROUTES
========================== */
const watchlistRoutes = require("./routes/watchlistRoutes");
const stockRoutes = require("./routes/stockRoutes");
const portfolioRoutes = require("./routes/portfolioRoutes");
const authRoutes = require("./routes/authRoutes");
const alertRoutes = require("./routes/alertRoutes");
const advisoryRoutes = require("./routes/advisoryRoutes");

/* ==========================
   SERVICES
========================== */

const { fetchAndStoreStocks } = require("./services/stockDataService");
const evaluateAlerts = require("./services/alertEngine");

const app = express();

/* ==========================
   MIDDLEWARE
========================== */

app.use(
  cors({
    origin: "http://localhost:5173",
    methods: ["GET", "POST", "PUT", "DELETE"],
    credentials: true,
  })
);

app.use(express.json());

/* ==========================
   HEALTH CHECK
========================== */

app.get("/", (req, res) => {
  res.status(200).json({
    success: true,
    message: "StockVision Backend Running 🚀",
  });
});

/* ==========================
   API ROUTES
========================== */

app.use("/api/stocks", stockRoutes);
app.use("/api/portfolio", portfolioRoutes);
app.use("/api/auth", authRoutes);
app.use("/api/alerts", alertRoutes);   // ✅ ALERT ROUTE ADDED
app.use("/api/advisory", advisoryRoutes);   // ✅ ADVISORY ROUTE ADDED
app.use("/api/watchlist", watchlistRoutes);   // ✅ WATCHLIST ROUTE ADDED

/* ==========================
   ALERT ENGINE CRON
========================== */

// Runs every 1 minute
cron.schedule("*/1 * * * *", async () => {
  console.log("⏳ Running alert evaluation...");
  await evaluateAlerts();
});

/* ==========================
   GLOBAL ERROR HANDLER
========================== */

app.use((err, req, res, next) => {
  console.error("Global Error:", err.message);

  res.status(500).json({
    success: false,
    message: err.message || "Internal Server Error",
  });
});

/* ==========================
   SERVER START
========================== */

const PORT = process.env.PORT || 5000;

app.listen(PORT, async () => {
  console.log(`🚀 Server running on port ${PORT}`);

  try {
    console.log("📡 Fetching stock data...");
    await fetchAndStoreStocks();
    console.log("✅ Stock data update completed.");
  } catch (error) {
    console.error("❌ Stock fetch failed:", error.message);
  }
});