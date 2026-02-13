from typing import List, Dict, Any
from utils.database import get_db_connection
from utils.logging_config import logger
from utils.exceptions import SystemException
from utils.retries import db_retry

class PortfolioService:
    @db_retry
    def get_portfolio(self, user_id: int = 1) -> List[Dict[str, Any]]:
        portfolio_id = user_id # Simplified for demo
        try:
            conn = get_db_connection()
            
            # Ensure portfolio exists
            p_check = conn.execute("SELECT id FROM portfolios WHERE id = ?", (portfolio_id,)).fetchone()
            if not p_check:
                logger.info(f"Creating default portfolio for user {user_id}")
                conn.execute("INSERT INTO portfolios (id, user_id, name) VALUES (?, ?, ?)", (portfolio_id, user_id, "My Portfolio"))
                conn.commit()

            sql = """
            SELECT 
                h.stock_id as symbol,
                h.quantity,
                h.avg_buy_price,
                s.price as current_price,
                s.company_name
            FROM portfolio_holdings h
            JOIN stocks s ON h.stock_id = s.symbol
            WHERE h.portfolio_id = ?
            """
            rows = conn.execute(sql, (portfolio_id,)).fetchall()
            conn.close()

            # Edge Case Handling: Empty portfolio or Null prices
            results = []
            for r in rows:
                d = dict(r)
                quantity = d.get('quantity', 0)
                avg_buy_price = d.get('avg_buy_price', 0)
                current_price = d.get('current_price')

                # Case 2: null stock price -> mark stock unavailable, skip P&L
                if current_price is None:
                    logger.warning(f"Stock {d.get('symbol')} has no current price. Skipping P&L calculation.")
                    d['profit_loss'] = 0.0
                    d['current_price'] = 0.0
                else:
                    d['profit_loss'] = (current_price - avg_buy_price) * quantity
                
                results.append(d)

            return results

        except Exception as e:
            logger.error(f"Portfolio fetch failure: {e}", exc_info=True)
            raise SystemException()

    @db_retry
    def add_to_portfolio(self, symbol: str, quantity: int, avg_buy_price: float, user_id: int = 1) -> Dict[str, Any]:
        portfolio_id = user_id
        try:
            conn = get_db_connection()
            
            # Check if stock exists
            stock = conn.execute("SELECT symbol FROM stocks WHERE symbol = ?", (symbol,)).fetchone()
            if not stock:
                conn.close()
                return {"status": "error", "message": f"Stock {symbol} not found in database."}

            # Check if holding exists
            holding = conn.execute(
                "SELECT quantity, avg_buy_price FROM portfolio_holdings WHERE portfolio_id = ? AND stock_id = ?", 
                (portfolio_id, symbol)
            ).fetchone()

            if holding:
                # Update existing holding (simplified: weighted average)
                old_qty = holding['quantity']
                old_price = holding['avg_buy_price']
                new_qty = old_qty + quantity
                new_price = ((old_qty * old_price) + (quantity * avg_buy_price)) / new_qty
                
                conn.execute(
                    "UPDATE portfolio_holdings SET quantity = ?, avg_buy_price = ? WHERE portfolio_id = ? AND stock_id = ?",
                    (new_qty, new_price, portfolio_id, symbol)
                )
            else:
                # Insert new holding
                conn.execute(
                    "INSERT INTO portfolio_holdings (portfolio_id, stock_id, quantity, avg_buy_price) VALUES (?, ?, ?, ?)",
                    (portfolio_id, symbol, quantity, avg_buy_price)
                )
            
            conn.commit()
            conn.close()
            return {"status": "success", "message": f"Added {quantity} shares of {symbol} to portfolio."}

        except Exception as e:
            logger.error(f"Portfolio add failure: {e}", exc_info=True)
            raise SystemException()

portfolio_service = PortfolioService()
