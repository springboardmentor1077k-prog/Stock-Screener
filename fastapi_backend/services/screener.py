import time
import json
from typing import List, Dict, Any
from utils.database import get_db_connection
from utils.logging_config import logger
from utils.exceptions import ComplianceException, SystemException, DatabaseException, ServiceException
from utils.retries import db_retry
from services.cache import cache_service

# Reusing AIBackend from current project
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Streamlit_Dashboard"))
from ai_service import AIBackend

class ScreenerService:
    def __init__(self):
        self.ai_backend = AIBackend()

    @db_retry
    def screen(self, query: str, sector: str, strong_only: bool, market_cap_filter: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 1. Cache Check
        cache_payload = {
            "query": query,
            "sector": sector,
            "strong_only": strong_only,
            "market_cap": market_cap_filter
        }
        cache_key = cache_service.make_key("screener", cache_payload)
        cached_data = cache_service.get(cache_key)
        if cached_data:
            cached_data["cached"] = True
            cached_data["latency_ms"] = int((time.time() - start_time) * 1000)
            return cached_data

        # 2. Logic Selection
        is_natural_language = len(query.split()) > 2 or any(k in query.lower() for k in ["show", "find", "where", "stocks", "sector", "price", "pe ratio"])

        try:
            if is_natural_language:
                ai_result = self.ai_backend.process_query(query)
                if not ai_result["is_valid"]:
                    logger.info(f"Compliance rejection for query: {query}")
                    raise ComplianceException()
                sql = ai_result["generated_sql"]
                params = []
            else:
                sql = "SELECT * FROM stocks WHERE 1=1"
                params = []
                if query:
                    try:
                        numeric_val = float(query)
                        sql += " AND (price > ? OR pe_ratio < ?)"
                        params.extend([numeric_val, numeric_val])
                    except ValueError:
                        sql += " AND (symbol LIKE ? OR company_name LIKE ?)"
                        params.extend([f"%{query}%", f"%{query}%"])
                
                if sector and sector != "All":
                    sql += " AND sector = ?"
                    params.append(sector)
                
                if strong_only:
                    sql += " AND pe_ratio < 30 AND price > 20"
                
                if market_cap_filter == "Large Cap (>10B)":
                    sql += " AND market_cap > 10"
                elif market_cap_filter == "Mid Cap (2B-10B)":
                    sql += " AND market_cap BETWEEN 2 AND 10"
                elif market_cap_filter == "Small Cap (<2B)":
                    sql += " AND market_cap < 2"

            # 3. DB Execution
            try:
                conn = get_db_connection()
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
            except Exception as db_err:
                logger.error(f"Database execution failed: {db_err}")
                raise DatabaseException(f"Failed to execute screening query: {str(db_err)}")

            # 4. Edge Case Handling: Partial Data
            results = []
            for r in rows:
                d = dict(r)
                # Ensure mandatory fields are present and valid
                if d.get('symbol') and d.get('price') is not None and d.get('market_cap') is not None:
                    results.append(d)
                else:
                    logger.warning(f"Excluding stock {d.get('symbol')} due to missing mandatory data")

            response_obj = {
                "status": "success",
                "data": results,
                "cached": False,
                "latency_ms": int((time.time() - start_time) * 1000)
            }

            # 5. Cache Result
            cache_service.set(cache_key, response_obj)
            return response_obj

        except ComplianceException:
            raise
        except Exception as e:
            logger.error(f"Screener logic failure: {e}", exc_info=True)
            raise SystemException()

screener_service = ScreenerService()
