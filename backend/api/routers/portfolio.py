# Portfolio API Router
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...models.schemas import PortfolioItem, PortfolioAddBySymbol
from ...database.connection import get_db
from ...services.portfolio_service import PortfolioService
from ...auth.jwt_handler import get_current_user
from ...models.database import User, MasterStock

portfolio_router = APIRouter()

@portfolio_router.get("/", response_model=List[PortfolioItem])
def get_portfolio(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get user's portfolio holdings.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = PortfolioService()
        return service.get_user_portfolio(current_user.user_id, db)
    except Exception as e:
        handle_database_error(e)


@portfolio_router.get("/with-quarterly-data")
def get_portfolio_with_quarterly_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get user's portfolio holdings with quarterly financial data.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = PortfolioService()
        return service.get_portfolio_with_quarterly_data(current_user.user_id, db)
    except Exception as e:
        handle_database_error(e)

@portfolio_router.post("/add")
def add_to_portfolio(portfolio_item: PortfolioItem, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Add a stock to user's portfolio.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = PortfolioService()
        success = service.add_stock_to_portfolio(current_user.user_id, portfolio_item.stock_id, portfolio_item.quantity, portfolio_item.avg_purchase_price, db)
        if success:
            return {"message": f"Added {portfolio_item.quantity} shares of stock {portfolio_item.stock_id} to portfolio"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add to portfolio")
    except Exception as e:
        handle_database_error(e)


@portfolio_router.post("/add-by-symbol")
def add_to_portfolio_by_symbol(
    item: PortfolioAddBySymbol,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a stock to the user's portfolio by symbol instead of internal stock_id.
    Resolves the symbol to a MasterStock entry and then delegates to the
    existing portfolio service.
    """
    from ...core.utils import handle_database_error
    from sqlalchemy.exc import SQLAlchemyError

    symbol = item.symbol.strip().upper()
    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Symbol must not be empty.",
        )

    try:
        stock = db.query(MasterStock).filter(MasterStock.symbol == symbol).first()
    except SQLAlchemyError as e:
        # True DB error
        handle_database_error(e, operation="lookup MasterStock by symbol")

    if not stock:
        # If the symbol hasn't been ingested yet, create a minimal master stock
        # entry so that portfolio tracking still works. Screener and analytics
        # will only be fully accurate once real fundamentals are ingested.
        try:
            stock = MasterStock(
                symbol=symbol,
                company_name=symbol,
                exchange="UNKNOWN",
                sector=None,
                industry=None,
                description=None,
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)
        except SQLAlchemyError as e:
            handle_database_error(e, operation="create MasterStock placeholder")

    try:
        service = PortfolioService()
        success = service.add_stock_to_portfolio(
            current_user.user_id,
            stock.stock_id,
            item.quantity,
            item.avg_purchase_price,
            db,
        )
    except SQLAlchemyError as e:
        handle_database_error(e, operation="add stock to portfolio")

    if success:
        return {
            "message": f"Added {item.quantity} shares of {symbol} to portfolio at average price {item.avg_purchase_price}."
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to add to portfolio")

@portfolio_router.delete("/{stock_id}")
def remove_from_portfolio(stock_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Remove a stock from user's portfolio.
    """
    from ...core.utils import handle_database_error
    
    try:
        service = PortfolioService()
        success = service.remove_stock_from_portfolio(current_user.user_id, stock_id, db)
        if success:
            return {"message": f"Removed stock {stock_id} from portfolio"}
        else:
            raise HTTPException(status_code=500, detail="Failed to remove from portfolio")
    except Exception as e:
        handle_database_error(e)

@portfolio_router.get("/summary")
def get_portfolio_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get portfolio summary (total value, P&L, etc.).
    """
    from ...core.utils import handle_database_error
    
    try:
        service = PortfolioService()
        return service.get_portfolio_summary(current_user.user_id, db)
    except Exception as e:
        handle_database_error(e)