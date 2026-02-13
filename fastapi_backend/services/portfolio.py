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

portfolio_service = PortfolioService()
