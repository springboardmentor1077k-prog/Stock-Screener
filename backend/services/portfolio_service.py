# Portfolio Service
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models.database import Portfolio, User, MasterStock, Fundamental, QuarterlyFinancial
from sqlalchemy import and_
import logging


logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self):
        pass
    
    def get_user_portfolio(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get user's portfolio holdings

        Uses LEFT JOINs so that holdings are visible even if we don't yet
        have fundamentals for a given stock (e.g. symbol was added manually).
        """
        portfolio_items = (
            db.query(Portfolio, MasterStock, Fundamental)
            .join(MasterStock, Portfolio.stock_id == MasterStock.stock_id)
            .outerjoin(Fundamental, Portfolio.stock_id == Fundamental.stock_id)
            .filter(Portfolio.user_id == user_id)
            .all()
        )
        
        results = []
        for portfolio_item, stock, fundamental in portfolio_items:
            try:
                avg_purchase_price = float(portfolio_item.avg_purchase_price) if portfolio_item.avg_purchase_price else None
                current_price = float(fundamental.current_price) if (fundamental and fundamental.current_price) else None
                total_value = (
                    float(portfolio_item.quantity * fundamental.current_price)
                    if (fundamental and fundamental.current_price)
                    else None
                )
            except (TypeError, ValueError):
                # Handle potential conversion errors
                avg_purchase_price = None
                current_price = None
                total_value = None
            
            results.append({
                "portfolio_id": portfolio_item.portfolio_id,
                "stock_id": stock.stock_id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "quantity": portfolio_item.quantity,
                "avg_purchase_price": avg_purchase_price,
                "current_price": current_price,
                "total_value": total_value,
            })
        
        return results
    
    def get_portfolio_with_quarterly_data(self, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get user's portfolio holdings with quarterly financial data"""
        # Get portfolio items with related data
        portfolio_items = db.query(Portfolio, MasterStock, Fundamental).\
            join(MasterStock, Portfolio.stock_id == MasterStock.stock_id).\
            join(Fundamental, Portfolio.stock_id == Fundamental.stock_id).\
            filter(Portfolio.user_id == user_id).\
            all()
        
        # Get all quarterly data for the portfolio stocks in a single query
        stock_ids = [stock.stock_id for _, stock, _ in portfolio_items]
        quarterly_data = db.query(QuarterlyFinancial).\
            filter(QuarterlyFinancial.stock_id.in_(stock_ids)).\
            order_by(QuarterlyFinancial.stock_id, QuarterlyFinancial.fiscal_year.desc(), QuarterlyFinancial.quarter_number.desc()).\
            all()
        
        # Group quarterly data by stock_id for easy lookup
        quarterly_by_stock = {}
        for qf in quarterly_data:
            if qf.stock_id not in quarterly_by_stock:
                quarterly_by_stock[qf.stock_id] = []
            quarterly_by_stock[qf.stock_id].append(qf)
        
        results = []
        for portfolio_item, stock, fundamental in portfolio_items:
            # Get quarterly financial data for this stock (take last 8 quarters)
            stock_quarterly_data = quarterly_by_stock.get(stock.stock_id, [])
            # Sort and limit to last 8 quarters
            stock_quarterly_data.sort(key=lambda x: (x.fiscal_year, x.quarter_number), reverse=True)
            stock_quarterly_data = stock_quarterly_data[:8]
            
            quarterly_list = []
            for qf in stock_quarterly_data:
                try:
                    quarterly_entry = {
                        'quarter': f"Q{qf.quarter_number} {qf.fiscal_year}",
                        'year': qf.fiscal_year,
                        'revenue': float(qf.revenue) if qf.revenue else 0,
                        'ebitda': float(qf.ebitda) if qf.ebitda else 0,
                        'net_profit': float(qf.net_profit) if qf.net_profit else 0,
                        'eps': float(qf.eps) if qf.eps else 0,
                        'free_cash_flow': float(qf.free_cash_flow) if qf.free_cash_flow else 0,
                        'reported_date': qf.reported_date.isoformat() if qf.reported_date else None,
                        'symbol': stock.symbol
                    }
                except (TypeError, ValueError):
                    # Handle potential conversion errors
                    quarterly_entry = {
                        'quarter': f"Q{getattr(qf, 'quarter_number', 'N/A')} {getattr(qf, 'fiscal_year', 'N/A')}",
                        'year': getattr(qf, 'fiscal_year', 'N/A'),
                        'revenue': 0,
                        'ebitda': 0,
                        'net_profit': 0,
                        'eps': 0,
                        'free_cash_flow': 0,
                        'reported_date': getattr(qf, 'reported_date', None) and getattr(qf.reported_date, 'isoformat', lambda: None)() or None,
                        'symbol': stock.symbol
                    }
                quarterly_list.append(quarterly_entry)
            
            try:
                avg_purchase_price = float(portfolio_item.avg_purchase_price) if portfolio_item.avg_purchase_price else None
                current_price = float(fundamental.current_price) if fundamental.current_price else None
                total_value = float(portfolio_item.quantity * fundamental.current_price) if fundamental.current_price else None
            except (TypeError, ValueError):
                # Handle potential conversion errors
                avg_purchase_price = None
                current_price = None
                total_value = None
            
            results.append({
                "portfolio_id": portfolio_item.portfolio_id,
                "stock_id": stock.stock_id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "quantity": portfolio_item.quantity,
                "avg_purchase_price": avg_purchase_price,
                "current_price": current_price,
                "total_value": total_value,
                "quarterly_data": quarterly_list
            })
        
        return results
    
    def add_stock_to_portfolio(self, user_id: str, stock_id: str, quantity: int, purchase_price: float, db: Session) -> bool:
        """Add a stock to user's portfolio"""
        try:
            # Check if stock already exists in portfolio
            existing_portfolio = db.query(Portfolio).filter(
                and_(Portfolio.user_id == user_id, Portfolio.stock_id == stock_id)
            ).first()
            
            if existing_portfolio:
                # Update existing position
                # Normalize types to floats to avoid Decimal/float mixing issues
                existing_qty = float(existing_portfolio.quantity or 0)
                existing_avg = float(existing_portfolio.avg_purchase_price or 0)
                add_qty = float(quantity)
                add_price = float(purchase_price)

                total_quantity = existing_qty + add_qty
                total_cost = (existing_qty * existing_avg) + (add_qty * add_price)
                new_avg_price = total_cost / total_quantity if total_quantity > 0 else add_price
                
                existing_portfolio.quantity = int(total_quantity)
                existing_portfolio.avg_purchase_price = new_avg_price
            else:
                # Create new portfolio entry
                portfolio_item = Portfolio(
                    user_id=user_id,
                    stock_id=stock_id,
                    quantity=quantity,
                    avg_purchase_price=purchase_price
                )
                db.add(portfolio_item)
            
            db.commit()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error adding stock to portfolio: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    def remove_stock_from_portfolio(self, user_id: str, stock_id: str, db: Session) -> bool:
        """Remove a stock from user's portfolio"""
        try:
            portfolio_item = db.query(Portfolio).filter(
                and_(Portfolio.user_id == user_id, Portfolio.stock_id == stock_id)
            ).first()
            
            if portfolio_item:
                db.delete(portfolio_item)
                db.commit()
            
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error removing stock from portfolio: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    def get_portfolio_summary(self, user_id: str, db: Session) -> Dict[str, Any]:
        """Get portfolio summary (total value, P&L, etc.)"""
        portfolio_items = db.query(Portfolio, Fundamental).\
            join(Fundamental, Portfolio.stock_id == Fundamental.stock_id).\
            filter(Portfolio.user_id == user_id).\
            all()
        
        total_value = 0
        total_cost = 0
        
        for portfolio_item, fundamental in portfolio_items:
            try:
                current_value = portfolio_item.quantity * float(fundamental.current_price) if fundamental.current_price else 0
                cost = portfolio_item.quantity * float(portfolio_item.avg_purchase_price) if portfolio_item.avg_purchase_price else 0
                
                total_value += current_value
                total_cost += cost
            except (TypeError, ValueError) as e:
                logger.warning(f"Error calculating portfolio value for stock {fundamental.stock_id if fundamental else 'Unknown'}: {str(e)}")
                continue  # Skip this item if there's a calculation error
        
        try:
            total_pnl = total_value - total_cost
            portfolio_return = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        except ZeroDivisionError:
            total_pnl = 0
            portfolio_return = 0
        
        return {
            "total_holdings": len(portfolio_items),
            "total_value": total_value,
            "total_cost": total_cost,
            "total_pnl": total_pnl,
            "portfolio_return": portfolio_return
        }