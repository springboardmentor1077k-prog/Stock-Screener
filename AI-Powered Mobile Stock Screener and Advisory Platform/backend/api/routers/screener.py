# Screener API Router
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
import re
from ...models.schemas import (
    ScreenerDSL,
    ScreenerResult,
    ScreenerRule,
    Condition,
    FinancialMetric,
    ConditionOperator,
)
from ...services.screener_engine import ScreenerEngineService
from ...auth.jwt_handler import get_current_user
from ...models.database import User

class ScreenerRequest(BaseModel):
    """Request payload for the /screen endpoint (JSON body)."""

    query: str
    sector: str = "All"
    strong_only: bool = True
    market_cap: str = "Any"


screener_router = APIRouter()

@screener_router.post("/parse", response_model=ScreenerDSL)
async def parse_screener_query(query: str, current_user: User = Depends(get_current_user)):
    """Parse a natural language query to structured DSL"""
    try:
        from ai_layer.llm_parser_service import parse_natural_language_query
        result = parse_natural_language_query(query)
        return result
    except Exception as e:
        from ...core.exceptions import InvalidQueryException
        raise InvalidQueryException(detail=f"Error parsing query: {str(e)}")


@screener_router.post("/search", response_model=List[ScreenerResult])
async def search_stocks(dsl: ScreenerDSL, current_user: User = Depends(get_current_user)):
    """Execute a screening query against the database"""
    from ...database.connection import get_db
    from ...core.utils import handle_database_error
    
    try:
        service = ScreenerEngineService()
        
        # Get a database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Execute the screener query
            results = service.execute_screener(dsl, db)
            return results
        finally:
            db.close()
    except Exception as e:
        handle_database_error(e)


@screener_router.post("/execute", response_model=List[ScreenerResult])
async def execute_screener(dsl: ScreenerDSL, current_user: User = Depends(get_current_user)):
    """Execute a screening query against the database (alias for search)"""
    from ...database.connection import get_db
    from ...core.utils import handle_database_error
    
    try:
        service = ScreenerEngineService()
        
        # Get a database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Execute the screener query
            results = service.execute_screener(dsl, db)
            return results
        finally:
            db.close()
    except Exception as e:
        handle_database_error(e)


@screener_router.post("/screen")
async def screen_stocks(
    request: ScreenerRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Screen stocks using natural language query (for frontend compatibility).

    This endpoint is user-facing and should return clear, structured error
    messages for invalid or unsupported queries instead of generic 5xx errors.
    """
    from ...database.connection import get_db
    from ...core.utils import handle_database_error
    from ...core.exceptions import InvalidQueryException
    from ai_layer.llm_parser_service import parse_natural_language_query
    import logging

    logger = logging.getLogger(__name__)

    # 1. Early validation layer: block unsupported / predictive queries
    invalid_keywords = [
        "predict",
        "forecast",
        "future",
        "next quarter",
        "next year",
        "will go up",
        "will go down",
        "should i buy",
        "should i sell",
        "recommend",
        "advice",
    ]

    cleaned_query = (request.query or "").strip()
    query_lower = cleaned_query.lower()

    for kw in invalid_keywords:
        if kw in query_lower:
            return {
                "status": "invalid_query",
                "message": "This screener only supports descriptive, data-filtering queries. "
                "Predictions and explicit buy/sell advice are intentionally blocked.",
                "reason": f"Detected unsupported intent related to '{kw}'.",
            }

    # 2. Try simple, built-in patterns before calling the LLM parser.
    #    This makes queries like "PE below 30" work even if the parser
    #    is unavailable or returns an empty DSL.
    dsl = None

    # Simple PE ratio pattern: "pe below 30", "pe < 30", "pe less than 30"
    pe_pattern = re.search(
        r"\bpe(?:\s*ratio)?\b[^\d<>]*(?:below|under|less than|<)\s*(\d+(\.\d+)?)",
        query_lower,
    )
    if pe_pattern:
        try:
            threshold = float(pe_pattern.group(1))
            dsl = ScreenerDSL(
                name="Simple PE filter",
                description=cleaned_query,
                rules=[
                    ScreenerRule(
                        conditions=[
                            Condition(
                                field=FinancialMetric.PE_RATIO,
                                operator=ConditionOperator.LESS_THAN,
                                value=threshold,
                            )
                        ],
                        logical_operator="AND",
                    )
                ],
                exchanges=None,
                sectors=None,
                industries=None,
            )
            logger.info(f"Using simple PE DSL fallback for query '{cleaned_query}' with threshold {threshold}")
        except ValueError:
            dsl = None

    try:
        # If no simple fallback matched, use the full LLM-based parser.
        if dsl is None:
            dsl = parse_natural_language_query(cleaned_query)

        service = ScreenerEngineService()

        # 3. Execute against the database
        db_gen = get_db()
        db = next(db_gen)

        try:
            results = service.execute_screener(dsl, db)

            if not results:
                # If nothing matched, try returning a small fallback universe so
                # the UI still has something to show and users can see that
                # data exists.
                from sqlalchemy import text

                fallback_sql = text(
                    "SELECT ms.symbol, ms.company_name, ms.exchange, "
                    "f.pe_ratio, f.current_price, f.market_cap "
                    "FROM master_stocks ms "
                    "LEFT JOIN fundamentals f ON ms.stock_id = f.stock_id "
                    "LIMIT 10"
                )
                result = db.execute(fallback_sql)
                fallback_rows = result.fetchall()
                if fallback_rows:
                    cols = list(result.keys())
                    fallback_data = [dict(zip(cols, row)) for row in fallback_rows]
                    return {
                        "status": "success",
                        "data": fallback_data,
                        "fallback": True,
                        "message": "No stocks matched your exact criteria. Showing a small sample universe instead.",
                    }

                # No rows matched and no fallback universe available
                return {
                    "status": "no_data",
                    "message": "No stocks matched your screening criteria. "
                    "Try relaxing one or two filters or broadening the sector/universe.",
                    "data": [],
                }

            return {"status": "success", "data": results}
        finally:
            db.close()
    except InvalidQueryException as e:
        # Structured invalid query from our own parser/validation
        logger.info(f"Invalid screener query: {e.detail}")
        return {
            "status": "invalid_query",
            "message": str(e.detail),
        }
    except ValueError as e:
        # Validation errors from ScreenerEngineService.validate_dsl
        logger.info(f"DSL validation error: {str(e)}")
        return {
            "status": "invalid_query",
            "message": str(e),
        }
    except Exception as e:
        # Unexpected / DB-related issues – keep existing centralized handling
        handle_database_error(e)

@screener_router.post("/compile", response_model=dict)
def compile_to_sql(dsl: ScreenerDSL, current_user: User = Depends(get_current_user)):
    """
    Compile a DSL query to SQL without executing it.
    """
    try:
        engine = ScreenerEngineService()
        validation_error = engine.validate_dsl(dsl)
        if validation_error:
            raise HTTPException(status_code=400, detail=validation_error)
        
        sql = engine.compile_to_sql(dsl)
        return {"sql": sql}
    except ValueError as e:
        from ...core.exceptions import InvalidQueryException
        raise InvalidQueryException(detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@screener_router.get("/examples", response_model=List[dict])
def get_example_queries(current_user: User = Depends(get_current_user)):
    """
    Get example queries for the UI.
    """
    examples = [
        {
            "name": "Low PE Stocks",
            "query": "Show me all stocks with PE ratio below 15"
        },
        {
            "name": "Growth Stocks",
            "query": "Show me stocks with PEG ratio below 1"
        },
        {
            "name": "High Cash Flow",
            "query": "Show me stocks with positive free cash flow"
        }
    ]
    return examples