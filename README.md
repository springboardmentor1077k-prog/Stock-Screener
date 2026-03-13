📈 StockVision – AI Powered Stock Analytics Platform

StockVision is a full-stack web application that helps users analyze stock market data, track investments, and monitor market movements in a simple and interactive way. The platform allows users to explore available stocks, create a watchlist, manage their investment portfolio, and receive intelligent insights.

This project demonstrates the integration of modern web technologies such as React, Node.js, Express, PostgreSQL, and external stock APIs to build a complete analytics platform.

🚀 Features
Dashboard
Provides an overview of the platform and quick navigation to major features.

AI Stock Screener
Allows users to filter and discover stocks based on predefined conditions.

All Stocks
Displays available stocks stored in the database with their current market prices.

Watchlist
Users can add stocks to a watchlist to monitor them without purchasing.

Portfolio Management
Users can add their stock holdings with quantity and purchase price.
The platform calculates total investment value and profit/loss.

Alerts
Users can create price alerts that trigger when a stock reaches a specific condition.

AI Advisory
Provides basic analysis and insights about selected stocks.

🛠️ Tech Stack
Frontend
React
React Router
Axios

CSS
Backend
Node.js
Express.js

Node Cron (for scheduled tasks)
Database
PostgreSQL

Other Tools
REST APIs
Git & GitHub
VS Code

📊 How to Use
1 Register or Login
Create an account to access the platform.

2 View Stocks
Navigate to All Stocks to see available stocks and prices.

3 Add to Watchlist
Add stocks you want to monitor.

4 Manage Portfolio
Go to Portfolio and add holdings by entering:
Stock symbol
Quantity
Buy price
The platform calculates investment value automatically.

5 Create Alerts
Set price alerts to track important market movements.

6 View Advisory
Check AI insights for selected stocks.

⏱ Automated Background Jobs

The backend uses node-cron to run scheduled tasks such as:
Fetching stock data
Evaluating alerts
Updating database records

## Dashboard
![Dashboard](assets/screenshots/dashboard-overview.png)

## Stock List
![Stock List](assets/screenshots/stock-list.png)

## Watchlist
![Watchlist](assets/screenshots/watchlist-page.png)

## Portfolio
![Portfolio](assets/screenshots/portfolio-tracker.png)