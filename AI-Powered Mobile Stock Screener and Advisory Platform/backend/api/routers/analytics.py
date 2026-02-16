"""
Analytics API Router
Provides endpoints for market analytics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from ...database.connection import get_db
from ...auth.jwt_handler import get_current_user
from ...models.database import User

analytics_router = APIRouter()

@analytics_router.get("/market-overview")
def get_market_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get market overview data including indices and sector performance.
    """
    from ...core.utils import handle_database_error
    
    try:
        # Mock market data - in a real application, this would fetch from external APIs
        market_data = {
            "indices": {
                "S&P 500": {"value": 4890.18, "change": "+0.34%"},
                "NASDAQ": {"value": 15657.82, "change": "+0.67%"},
                "DOW JONES": {"value": 38256.58, "change": "+0.12%"},
                "VIX": {"value": 15.42, "change": "-2.34%"}
            },
            "sectors": {
                "Technology": "+2.15%",
                "Healthcare": "+1.23%",
                "Financials": "+0.87%",
                "Consumer Discretionary": "+1.56%",
                "Energy": "-0.45%",
                "Utilities": "+0.32%"
            },
            "updated_at": "2023-07-25T16:30:00Z"
        }
        
        return market_data
    except Exception as e:
        handle_database_error(e)


@analytics_router.get("/portfolio-analysis")
def get_portfolio_analysis(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get portfolio analysis and insights for the current user.
    """
    from ...core.utils import handle_database_error
    from ...services.portfolio_service import PortfolioService
    
    try:
        service = PortfolioService()
        portfolio_data = service.get_user_portfolio(current_user.user_id, db)
        
        # Calculate portfolio insights
        if portfolio_data:
            total_value = sum(item.get('total_value', 0) for item in portfolio_data if item.get('total_value'))
            holdings_count = len(portfolio_data)
            
            # Identify top holdings by value
            sorted_holdings = sorted(
                portfolio_data, 
                key=lambda x: x.get('total_value', 0), 
                reverse=True
            )[:5]  # Top 5 holdings
            
            analysis = {
                "total_value": total_value,
                "holdings_count": holdings_count,
                "top_holdings": [
                    {
                        "symbol": item.get('symbol'),
                        "company_name": item.get('company_name'),
                        "value": item.get('total_value', 0),
                        "percentage": round((item.get('total_value', 0) / total_value * 100) if total_value > 0 else 0, 2)
                    } 
                    for item in sorted_holdings if item.get('total_value', 0) > 0
                ],
                "sector_diversification": {}  # Would calculate from holdings in a real implementation
            }
        else:
            analysis = {
                "total_value": 0,
                "holdings_count": 0,
                "top_holdings": [],
                "sector_diversification": {}
            }
        
        return analysis
    except Exception as e:
        handle_database_error(e)


@analytics_router.get("/sector-performance")
def get_sector_performance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get sector performance data.
    """
    from ...core.utils import handle_database_error
    
    try:
        # Mock sector performance data - in a real application, this would fetch from external APIs
        sector_data = {
            "sectors": [
                {"name": "Technology", "performance": 2.15, "ytd": 15.32},
                {"name": "Healthcare", "performance": 1.23, "ytd": 8.45},
                {"name": "Financials", "performance": 0.87, "ytd": 12.67},
                {"name": "Consumer Discretionary", "performance": 1.56, "ytd": 18.23},
                {"name": "Energy", "performance": -0.45, "ytd": 35.67},
                {"name": "Utilities", "performance": 0.32, "ytd": 5.21},
                {"name": "Industrials", "performance": 0.76, "ytd": 9.87},
                {"name": "Materials", "performance": 0.54, "ytd": 11.34}
            ],
            "updated_at": "2023-07-25T16:30:00Z"
        }
        
        return sector_data
    except Exception as e:
        handle_database_error(e)