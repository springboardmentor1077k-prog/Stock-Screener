from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import uuid
import logging
from typing import Optional
from auth_utils import hash_password, verify_password, create_jwt_token, decode_jwt_token
from error_handlers import (
    ValidationError, AppSystemError, NotFoundError, AppError,
    format_error_response, retry_on_failure, safe_db_call
)

from llm_integration import english_to_dsl
from validator import validate_dsl
from screener_service import run_query
from alerts_service import alert_service
from db import get_db


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Stock Screener")


def list_response(resource_key: str, items):
    """Standardized list response shape with backward-compatible keys."""
    safe_items = items or []
    return {
        "status": "success",
        "count": len(safe_items),
        "total": len(safe_items),
        "items": safe_items,
        resource_key: safe_items
    }

# ============ CORS MIDDLEWARE ============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ GLOBAL EXCEPTION HANDLERS ============

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors with user-friendly messages."""
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=400,
        content=format_error_response(exc)
    )

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors."""
    logger.warning(f"Resource not found: {exc.message}")
    return JSONResponse(
        status_code=404,
        content=format_error_response(exc)
    )

@app.exception_handler(AppSystemError)
async def system_error_handler(request: Request, exc: AppSystemError):
    """Handle system errors with retry suggestion."""
    logger.error(f"System error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content=format_error_response(exc)
    )

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle generic app errors."""
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content=format_error_response(exc)
    )

# ---------------- AUTHENTICATION ----------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/register")
def register(data: RegisterRequest):
    """
    Register a new user with email and password.
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password and create user
        hashed_pw = hash_password(data.password)
        cursor.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (%s, %s, NOW())",
            (data.email, hashed_pw)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        # Create default portfolio for new user
        cursor.execute(
            "INSERT INTO portfolios (user_id, name, created_at) VALUES (%s, %s, NOW())",
            (user_id, "My Portfolio")
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "User registered successfully",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(data: LoginRequest):
    """
    Login with email and password, returns JWT token.
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Find user by email
        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = %s",
            (data.email,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate JWT token
        token = create_jwt_token(user['id'], user['email'])
        
        return {
            "access_token": token,
            "user_id": user['id'],
            "email": user['email']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def verify_token(authorization: str = Header(None)):
    """
    Verify JWT token and return user_id.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    payload = decode_jwt_token(authorization)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload['user_id']

# ---------------- SCREENING ----------------

class ScreenRequest(BaseModel):
    text: str

@app.post("/screen")
def screen(request: ScreenRequest, user=Depends(verify_token)):
    """
    Delegates to screener_service which handles:
    1. English query → DSL (Ollama)
    2. Validate DSL
    3. Compile DSL → SQL
    4. Execute SQL on MySQL
    """
    
    query = (request.text or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = run_query(query)
    
    if result.get("status") == "error":
         raise HTTPException(status_code=400, detail=result.get("message"))

    rows = result.get("rows", []) or []
    count = result.get("count", len(rows))
    return {
        "status": "success",
        "message": f"Found {count} matching stock(s)",
        "count": count,
        "total": count,
        "items": rows,
        "rows": rows
    }


# ---------------- SCREENER (with error handling) ----------------

class ScreenerRequest(BaseModel):
    query: str


@app.post("/screener")
def screen_stocks(data: ScreenerRequest, user_id: int = Depends(verify_token)):
    """
    Screen stocks using natural language query with comprehensive error handling.
    
    Edge cases handled:
    - Empty query
    - No results found
    - Invalid DSL
    - Database errors
    """
    try:
        # Validate query is not empty
        query = data.query.strip() if data.query else ""
        if not query:
            raise ValidationError(
                "Query cannot be empty",
                details="Please enter a valid screening query like 'PE ratio less than 25'"
            )
        
        logger.info(f"Screening request from user {user_id}: {query}")
        
        # Convert natural language to DSL
        try:
            dsl = english_to_dsl(query)
        except Exception as e:
            logger.error(f"LLM conversion failed: {str(e)}")
            raise ValidationError(
                "Could not understand query",
                details="Please rephrase your query more clearly"
            )
        
        # Validate DSL (will raise ValidationError if invalid)
        is_valid, error_msg = validate_dsl(dsl)
        if not is_valid:
            raise ValidationError(
                "Invalid query structure",
                details=error_msg or "Please simplify your query"
            )
        
        # Execute query using the full pipeline (NL → DSL → SQL → results)
        @retry_on_failure(max_attempts=3, delay=0.5)
        def execute_screener_query():
            with safe_db_call("Stock screening"):
                return run_query(query)
        
        result = execute_screener_query()
        
        if result.get("status") == "error":
            raise ValidationError(
                result.get("message", "Query failed"),
                details="Please try a different query"
            )
        
        count = result.get("count", 0)
        rows = result.get("rows", [])
        
        # Edge case: No results found
        if count == 0:
            logger.info(f"No stocks matched query: {query}")
            return {
                "status": "success",
                "message": "No stocks found matching your criteria",
                "count": 0,
                "total": 0,
                "items": [],
                "rows": [],
                "details": "Try adjusting your filters or using different metrics"
            }
        
        # Success with results
        logger.info(f"Found {count} stocks for query: {query}")
        return {
            "status": "success",
            "message": f"Found {count} matching stock(s)",
            "count": count,
            "total": count,
            "items": rows,
            "rows": rows
        }
    
    except ValidationError:
        # Re-raise validation errors to be handled by global handler
        raise
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Unexpected error - log and return generic message
        logger.error(f"Unexpected error in screener: {str(e)}", exc_info=True)
        raise AppSystemError(
            "Screening failed",
            details="Please try again. If the issue persists, try a simpler query."
        )


# ---------------- ALERTS ----------------

class AlertRequest(BaseModel):
    portfolio_id: Optional[int] = None
    metric: str
    operator: str
    threshold: float


@app.get("/alerts")
def get_alerts(user_id: int = Depends(verify_token)):
    """Get all alerts for the authenticated user."""
    try:
        success, message, alerts = alert_service.get_user_alerts(user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return list_response("alerts", alerts)
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts")
def create_alert(data: AlertRequest, user_id: int = Depends(verify_token)):
    """Create a new database-wide alert."""
    try:
        success, message, alert_id = alert_service.create_alert(
            user_id=user_id,
            portfolio_id=data.portfolio_id,
            metric=data.metric,
            operator=data.operator,
            threshold=data.threshold
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "status": "success",
            "message": message,
            "alert_id": alert_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/evaluate")
def evaluate_alerts(user_id: int = Depends(verify_token)):
    """
    Manually trigger alert evaluation for the authenticated user.
    Returns list of alerts that were triggered.
    """
    try:
        success, message, triggered = alert_service.evaluate_alerts(user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        already_triggered = 0
        if hasattr(alert_service, "last_eval_metrics"):
            already_triggered = alert_service.last_eval_metrics.get("already_triggered_recently", 0)

        return {
            "status": "success",
            "message": message,
            "triggered_count": len(triggered),
            "already_triggered_count": already_triggered,
            "total": len(triggered),
            "items": triggered,
            "triggered_alerts": triggered
        }
    except Exception as e:
        logger.error(f"Error evaluating alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, user_id: int = Depends(verify_token)):
    """
    Delete an alert by ID (only if owned by user).
    """
    try:
        success, message = alert_service.delete_alert(alert_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=message)
        
        return {
            "status": "success",
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- STOCKS LIST ----------------

@app.get("/stocks")
def get_stocks(user=Depends(verify_token)):
    """
    Get all available stocks for selection.
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                s.id,
                s.symbol,
                s.company_name,
                s.sector
            FROM stocks_master s
            ORDER BY s.symbol
        """)
        
        stocks = cursor.fetchall()
        conn.close()
        
        return list_response("stocks", stocks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- PORTFOLIO MANAGEMENT ----------------

@app.get("/portfolios")
def get_portfolios(user_id: int = Depends(verify_token)):
    """
    Get all portfolios for the authenticated user with stock counts.
    """
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get portfolios with stock counts using LEFT JOIN
        cursor.execute("""
            SELECT 
                p.id, 
                p.name, 
                p.created_at,
                COUNT(ph.id) as stock_count
            FROM portfolios p
            LEFT JOIN portfolio_holdings ph ON p.id = ph.portfolio_id
            WHERE p.user_id = %s
            GROUP BY p.id, p.name, p.created_at
            ORDER BY p.created_at DESC
        """, (user_id,))
        
        portfolios = cursor.fetchall()
        conn.close()
        
        return list_response("portfolios", portfolios)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolios/{portfolio_id}/holdings")
def get_portfolio_holdings(portfolio_id: int, user=Depends(verify_token)):
    """
    Get all stocks in a portfolio.
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Backend-owned authorization: verify portfolio belongs to user.
        cursor.execute(
            "SELECT id FROM portfolios WHERE id = %s AND user_id = %s",
            (portfolio_id, user)
        )
        portfolio = cursor.fetchone()
        if not portfolio:
            conn.close()
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        cursor.execute("""
            SELECT 
                ph.id,
                ph.stock_id,
                s.symbol,
                s.company_name,
                ph.quantity,
                ph.avg_buy_price,
                ph.created_at
            FROM portfolio_holdings ph
            JOIN stocks_master s ON ph.stock_id = s.id
            WHERE ph.portfolio_id = %s
            ORDER BY ph.created_at DESC
        """, (portfolio_id,))
        
        holdings = cursor.fetchall()
        conn.close()
        
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "count": len(holdings),
            "total": len(holdings),
            "items": holdings,
            "holdings": holdings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddHoldingRequest(BaseModel):
    portfolio_id: int
    stock_symbol: str
    quantity: int


@app.post("/portfolios/holdings")
def add_holding(request: AddHoldingRequest, user=Depends(verify_token)):
    """
    Add a stock to a portfolio.
    Price is automatically fetched from analyst_targets table.
    """
    try:
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

        symbol = (request.stock_symbol or "").strip().upper()
        if not symbol:
            raise HTTPException(status_code=400, detail="Stock symbol is required")

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Backend-owned authorization: validate portfolio ownership.
        cursor.execute(
            "SELECT id FROM portfolios WHERE id = %s AND user_id = %s",
            (request.portfolio_id, user)
        )
        portfolio = cursor.fetchone()
        if not portfolio:
            conn.close()
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get stock_id and current market price from database
        cursor.execute("""
            SELECT 
                s.id,
                a.current_market_price
            FROM stocks_master s
            LEFT JOIN analyst_targets a ON s.id = a.stock_id
            WHERE s.symbol = %s
        """, (symbol,))
        
        stock_data = cursor.fetchone()
        
        if not stock_data:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        stock_id = stock_data['id']
        current_price = stock_data.get('current_market_price')
        
        if not current_price:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Price data not available for {symbol}")
        
        # Insert or update holding with auto-fetched price
        cursor.execute("""
            INSERT INTO portfolio_holdings (portfolio_id, stock_id, quantity, avg_buy_price)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                quantity = %s,
                avg_buy_price = %s,
                updated_at = CURRENT_TIMESTAMP
        """, (request.portfolio_id, stock_id, request.quantity, current_price,
                request.quantity, current_price))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Added {symbol} to portfolio {request.portfolio_id} at ${current_price:.2f}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/portfolios/holdings/{holding_id}")
def remove_holding(holding_id: int, user=Depends(verify_token)):
    """
    Remove a stock from a portfolio.
    """
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Backend-owned authorization: ensure the holding belongs to user's portfolio.
        cursor.execute("""
            SELECT ph.id
            FROM portfolio_holdings ph
            JOIN portfolios p ON ph.portfolio_id = p.id
            WHERE ph.id = %s AND p.user_id = %s
        """, (holding_id, user))
        holding = cursor.fetchone()
        if not holding:
            conn.close()
            raise HTTPException(status_code=404, detail="Holding not found")

        cursor.execute(
            "DELETE FROM portfolio_holdings WHERE id = %s",
            (holding_id,)
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if affected > 0:
            return {
                "status": "success",
                "message": "Holding removed"
            }
        else:
            raise HTTPException(status_code=404, detail="Holding not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
