"""
Data Ingestion Service
Handles ingesting financial data from Alpha Vantage API into the database
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from decimal import Decimal
from .data_fetcher_service import data_fetcher_service
from ..models.database import MasterStock, Fundamental, QuarterlyFinancial
from ..core.utils import sanitize_input, format_financial_metric

logger = logging.getLogger(__name__)

class DataIngestionService:
    def __init__(self):
        pass

    def _upsert_master_stock(self, db: Session, symbol: str, company_data: Dict[str, Any]) -> MasterStock:
        """Insert or update master stock information"""
        # Check if stock already exists
        existing_stock = db.query(MasterStock).filter(MasterStock.symbol == symbol).first()
        
        if existing_stock:
            # Update existing record
            existing_stock.company_name = company_data.get('Name', existing_stock.company_name)
            existing_stock.exchange = company_data.get('Exchange', existing_stock.exchange)
            existing_stock.sector = company_data.get('Sector', existing_stock.sector)
            existing_stock.industry = company_data.get('Industry', existing_stock.industry)
            existing_stock.description = company_data.get('Description', existing_stock.description)
            db.commit()
            return existing_stock
        else:
            # Create new record
            stock = MasterStock(
                symbol=symbol,
                company_name=company_data.get('Name'),
                exchange=company_data.get('Exchange'),
                sector=company_data.get('Sector'),
                industry=company_data.get('Industry'),
                description=company_data.get('Description')
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)
            return stock

    def _upsert_fundamental_data(self, db: Session, stock_id: str, fundamental_data: Dict[str, Any]):
        """Insert or update fundamental data for a stock"""
        # Prepare fundamental data
        fundamental = {
            'pe_ratio': fundamental_data.get('PERatio'),
            'peg_ratio': fundamental_data.get('PEGRatio'),
            'ebitda': fundamental_data.get('EBITDA'),
            'free_cash_flow': fundamental_data.get('OperatingCashFlow'),  # Using OperatingCashFlow as proxy
            'promoter_holding': None,  # This isn't available in Alpha Vantage
            'debt_to_free_cash_flow': fundamental_data.get('TotalDebt'),
            'revenue_growth_yoy': fundamental_data.get('RevenueTTM'),
            'ebitda_growth_yoy': fundamental_data.get('EBITDATTM'),
            'earnings_growth_yoy': fundamental_data.get('EPS'),
            'current_price': fundamental_data.get('Price'),
            'market_cap': fundamental_data.get('MarketCapitalization'),
            'eps': fundamental_data.get('EPS'),
            'book_value': fundamental_data.get('BookValuePerShare'),
            'roe': fundamental_data.get('ReturnOnEquityTTM'),
            'roa': fundamental_data.get('ReturnOnAssetsTTM'),
            'dividend_yield': fundamental_data.get('DividendYield')
        }
        
        # Convert string values to appropriate types and handle missing values
        for key, value in fundamental.items():
            if value in ['None', None, '', 'None', 'null']:
                fundamental[key] = None
            else:
                try:
                    if key in ['pe_ratio', 'peg_ratio', 'dividend_yield', 'roe', 'roa', 'book_value', 'eps']:
                        fundamental[key] = Decimal(str(float(value))) if value and str(value).strip() != '' else None
                    elif key in ['ebitda', 'free_cash_flow', 'debt_to_free_cash_flow', 'revenue_growth_yoy', 
                                'ebitda_growth_yoy', 'earnings_growth_yoy', 'current_price', 'market_cap']:
                        fundamental[key] = Decimal(str(float(value))) if value and str(value).strip() != '' else None
                except (ValueError, TypeError, AttributeError):
                    fundamental[key] = None
        
        # Check if fundamental data already exists for this stock
        existing_fundamental = db.query(Fundamental).filter(Fundamental.stock_id == stock_id).first()
        
        if existing_fundamental:
            # Update existing record
            for key, value in fundamental.items():
                setattr(existing_fundamental, key, value)
            existing_fundamental.last_updated_date = datetime.now().date()
            db.commit()
        else:
            # Create new record
            fundamental_record = Fundamental(
                stock_id=stock_id,
                pe_ratio=fundamental['pe_ratio'],
                peg_ratio=fundamental['peg_ratio'],
                ebitda=fundamental['ebitda'],
                free_cash_flow=fundamental['free_cash_flow'],
                promoter_holding=fundamental['promoter_holding'],
                debt_to_free_cash_flow=fundamental['debt_to_free_cash_flow'],
                revenue_growth_yoy=fundamental['revenue_growth_yoy'],
                ebitda_growth_yoy=fundamental['ebitda_growth_yoy'],
                earnings_growth_yoy=fundamental['earnings_growth_yoy'],
                current_price=fundamental['current_price'],
                market_cap=fundamental['market_cap'],
                eps=fundamental['eps'],
                book_value=fundamental['book_value'],
                roe=fundamental['roe'],
                roa=fundamental['roa'],
                dividend_yield=fundamental['dividend_yield'],
                last_updated_date=datetime.now().date()
            )
            db.add(fundamental_record)
            db.commit()

    def _ingest_quarterly_financials(self, db: Session, stock_id: str, income_statement_data: Dict[str, Any]):
        """Ingest quarterly financial data from income statement"""
        if not income_statement_data or 'quarterlyReports' not in income_statement_data:
            logger.warning(f"No quarterly reports found for stock {stock_id}")
            return
        
        quarterly_reports = income_statement_data.get('quarterlyReports', [])
        
        for report in quarterly_reports:
            fiscal_date = report.get('fiscalDateEnding')
            if not fiscal_date:
                continue
            
            # Parse fiscal date
            try:
                fiscal_datetime = datetime.strptime(fiscal_date, '%Y-%m-%d')
                year = fiscal_datetime.year
                month = fiscal_datetime.month
                quarter = (month - 1) // 3 + 1
            except ValueError:
                continue  # Skip if date format is invalid
            
            # Prepare financial data
            revenue = report.get('totalRevenue')
            ebitda = report.get('ebitda')
            net_income = report.get('netIncome')
            
            # Convert to appropriate types
            try:
                revenue = Decimal(revenue) if revenue and revenue != 'None' else None
                ebitda = Decimal(ebitda) if ebitda and ebitda != 'None' else None
                net_income = Decimal(net_income) if net_income and net_income != 'None' else None
            except (ValueError, TypeError):
                continue  # Skip if conversion fails
            
            # Check if this quarterly record already exists
            existing_report = db.query(QuarterlyFinancial).filter(
                QuarterlyFinancial.stock_id == stock_id,
                QuarterlyFinancial.fiscal_year == year,
                QuarterlyFinancial.quarter_number == quarter
            ).first()
            
            if existing_report:
                # Update existing record
                existing_report.revenue = revenue
                existing_report.ebitda = ebitda
                existing_report.net_profit = net_income  # Changed from net_income to net_profit to match schema
                existing_report.reported_date = fiscal_datetime.date()
            else:
                # Create new record
                quarterly_record = QuarterlyFinancial(
                    stock_id=stock_id,
                    fiscal_year=year,
                    quarter_number=quarter,
                    revenue=revenue,
                    ebitda=ebitda,
                    net_profit=net_income,  # Changed from net_income to net_profit to match schema
                    eps=None,  # Not available from income statement
                    free_cash_flow=None,  # Not available from income statement
                    reported_date=fiscal_datetime.date()
                )
                db.add(quarterly_record)
        
        db.commit()

    def ingest_stock_data(self, db: Session, symbol: str) -> bool:
        """
        Main method to ingest all data for a given stock symbol
        """
        symbol = sanitize_input(symbol).upper()
        
        if not symbol:
            logger.error("Invalid symbol provided for data ingestion")
            return False
        
        try:
            logger.info(f"Starting data ingestion for symbol: {symbol}")
            
            # 1. Get company overview data
            company_data = data_fetcher_service.get_company_overview(symbol)
            if not company_data:
                logger.error(f"Failed to fetch company overview for {symbol}")
                return False
            
            # 2. Upsert master stock data
            master_stock = self._upsert_master_stock(db, symbol, company_data)
            
            # 3. Ingest fundamental data using overview data
            self._upsert_fundamental_data(db, master_stock.stock_id, company_data)
            
            # 4. Get and ingest quarterly financials
            income_statement_data = data_fetcher_service.get_income_statement(symbol)
            if income_statement_data:
                self._ingest_quarterly_financials(db, master_stock.stock_id, income_statement_data)
            else:
                logger.warning(f"No income statement data available for {symbol}")
            
            logger.info(f"Successfully completed data ingestion for symbol: {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error during data ingestion for {symbol}: {str(e)}", exc_info=True)
            db.rollback()
            return False

    def bulk_ingest_stocks(self, db: Session, symbols: List[str]) -> Dict[str, bool]:
        """
        Ingest data for multiple stock symbols
        """
        results = {}
        
        for symbol in symbols:
            try:
                success = self.ingest_stock_data(db, symbol)
                results[symbol] = success
            except Exception as e:
                logger.error(f"Error during bulk ingestion for {symbol}: {str(e)}", exc_info=True)
                results[symbol] = False
        
        return results

# Global instance of the data ingestion service
data_ingestion_service = DataIngestionService()

def ingest_stock_data(db: Session, symbol: str) -> bool:
    """Convenience function to ingest stock data"""
    return data_ingestion_service.ingest_stock_data(db, symbol)

def bulk_ingest_stocks(db: Session, symbols: List[str]) -> Dict[str, bool]:
    """Convenience function for bulk stock ingestion"""
    return data_ingestion_service.bulk_ingest_stocks(db, symbols)