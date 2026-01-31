import typing
import json
import os
from typing import Any, Dict, List, Tuple, Optional

def compile_condition(field: str, value: Any) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Compiles a single DSL condition into a SQL WHERE clause fragment and associated parameters.
    
    Args:
        field: The field name from the DSL.
        value: The value for the condition.
        
    Returns:
        A tuple containing:
        - The SQL fragment string (or None if field is unknown).
        - A dictionary of parameters to bind.
    """
    params = {}
    
    if field == "industry_category":
        # Example: sector = 'Technology'
        # We use a unique key for the parameter to avoid collisions if reused (though unlikely here)
        param_key = f"param_{field}"
        params[param_key] = value
        return f"sector = %({param_key})s", params
    
    if field == "peg_ratio_max":
        param_key = f"param_{field}"
        params[param_key] = value
        return f"peg < %({param_key})s", params
    
    if field == "fcf_to_debt_min":
        # (CASE WHEN debt = 0 THEN 0 ELSE fcf / debt END) >= 0.25
        param_key = f"param_{field}"
        params[param_key] = value
        return f"(CASE WHEN debt = 0 THEN 0 ELSE fcf / debt END) >= %({param_key})s", params
         
    if field == "price_vs_target":
        # This involves comparing columns, not binding a value directly.
        # DSL value examples: "<= target_low", "<= target_mean"
        if value == "<= target_low":
            return "price <= target_low", {}
        elif value == "<= target_mean":
            return "price <= target_mean", {}
        else:
            # Default fallback
            return "price <= target_low", {}
            
    if field == "revenue_yoy_positive":
        if value:
            return "rev_yoy > 0", {}
        return None, {}
        
    if field == "ebitda_yoy_positive":
        if value:
            return "ebitda_yoy > 0", {}
        return None, {}
        
    if field == "earnings_beat_likely":
        if value:
            # Assuming 'beats' column tracks number of recent beats
            # Hardcoded logic as per reference implementation
            return "beats >= 3", {}
        return None, {}
        
    if field == "buyback_announced":
        if value:
            return "buyback = TRUE", {}
        return "buyback = FALSE", {}
        
    if field == "next_earnings_within_days":
        param_key = f"param_{field}"
        params[param_key] = value
        return f"next_earnings_days <= %({param_key})s", params
        
    return None, {}

def compile_last_n_quarters_condition(value: Any) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Generates a SQL LIMIT clause based on the last n quarters condition.
    Assumption: 'last n quarters' implies limiting the result set to n rows, 
    potentially ordered by date if a date column existed. 
    Here it maps to a simple LIMIT clause.
    """
    params = {}
    if isinstance(value, int) and value > 0:
        param_key = "limit_n"
        params[param_key] = value
        return f"LIMIT %({param_key})s", params
    return None, {}

def compile_dsl_to_sql(dsl: Dict[str, Any], table_name: str = "stocks") -> Tuple[str, Dict[str, Any]]:
    """
    Compiles the full DSL dictionary into a complete SQL query with bound parameters.
    
    Args:
        dsl: The DSL dictionary.
        table_name: The name of the database table.
        
    Returns:
        A tuple containing:
        - The complete SQL SELECT statement.
        - The dictionary of parameters to bind.
    """
    conditions = []
    all_params = {}
    limit_clause = ""
    
    # Handle top-level fields
    if "industry_category" in dsl:
        cond, params = compile_condition("industry_category", dsl["industry_category"])
        if cond:
            conditions.append(cond)
            all_params.update(params)
            
    # Handle filters
    if "filters" in dsl and isinstance(dsl["filters"], dict):
        for key, val in dsl["filters"].items():
            cond, params = compile_condition(key, val)
            if cond:
                conditions.append(cond)
                all_params.update(params)
    
    # Handle last n quarters condition (Limit)
    if "last_n_quarters" in dsl:
        limit_str, limit_params = compile_last_n_quarters_condition(dsl["last_n_quarters"])
        if limit_str:
            limit_clause = " " + limit_str
            all_params.update(limit_params)
                
    where_clause = " AND ".join(conditions)
    
    if where_clause:
        sql = f"SELECT * FROM {table_name} WHERE {where_clause}{limit_clause};"
    else:
        sql = f"SELECT * FROM {table_name}{limit_clause};"
        
    return sql, all_params

def execute_screener(dsl: Dict[str, Any], db_connection: Any) -> List[Dict[str, Any]]:
    """
    Builds the SQL query from DSL and executes it against the provided database connection.
    
    Args:
        dsl: The DSL dictionary representing the screening criteria.
        db_connection: A database connection object (must support cursor() and dict-like rows or we convert them).
                       Assumes DB-API 2.0 compatibility (e.g., psycopg2, sqlite3).
        
    Returns:
        A list of dictionaries representing the rows found.
    """
    # 1. Compile DSL to SQL
    sql, params = compile_dsl_to_sql(dsl)
    
    # 2. Execute Query
    try:
        # Using a context manager for the cursor is good practice
        cursor = db_connection.cursor()
        
        # Execute with parameters
        cursor.execute(sql, params)
        
        # 3. Fetch and Format Results
        # If the cursor returns objects that aren't dicts, we might need to convert them.
        # Assuming psycopg2 with RealDictCursor or similar that allows fetching column names.
        
        if hasattr(cursor, 'description') and cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            result_list = []
            for row in rows:
                # If row is already a dict-like object (e.g. RealDictRow), use it directly or convert to dict
                if isinstance(row, dict):
                    result_list.append(dict(row))
                else:
                    # Zip columns with values
                    result_list.append(dict(zip(columns, row)))
            
            cursor.close()
            return result_list
        else:
            # Should not happen for SELECT
            cursor.close()
            return []
            
    except Exception as e:
        print(f"Error executing query: {e}")
        # Depending on requirements, might want to re-raise or return empty list
        raise e

def save_results_to_file(results: List[Dict[str, Any]], file_path: str):
    """
    Saves the list of dictionaries to a JSON file.
    
    Args:
        results: The list of dictionaries to save.
        file_path: The absolute or relative path to the output file.
    """
    # Ensure directory exists
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
        
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {os.path.abspath(file_path)}")

# --- Mocking for demonstration/testing purposes ---

class MockCursor:
    def __init__(self):
        self.description = [
            ("symbol",), ("sector",), ("price",), ("peg",), ("debt",), ("fcf",), ("rev_yoy",), ("ebitda_yoy",), ("beats",), ("buyback",), ("next_earnings_days",), ("target_low",)
        ]
        
    def execute(self, sql, params):
        print(f"\n[MockDB] Executing SQL: {sql}")
        print(f"[MockDB] With Params: {params}")
        
    def fetchall(self):
        # Return dummy data matching the criteria loosely
        return [
            ("NVDA", "Information Technology", 120.5, 2.1, 500, 2000, 15.5, 20.2, 4, True, 25, 130.0),
            ("AMD", "Information Technology", 160.0, 2.5, 300, 1200, 10.1, 12.0, 3, False, 20, 170.0)
        ]
    
    def close(self):
        pass

class MockConnection:
    def cursor(self):
        return MockCursor()

if __name__ == "__main__":
    # Example Usage
    sample_dsl = {
        "industry_category": "Information Technology",
        "filters": {
            "peg_ratio_max": 3.0,
            "fcf_to_debt_min": 0.25,
            "price_vs_target": "<= target_low",
            "revenue_yoy_positive": True,
            "ebitda_yoy_positive": True,
            "earnings_beat_likely": True,
            "buyback_announced": True,
            "next_earnings_within_days": 30
        }
    }
    
    print("--- Running Screener with Mock DB ---")
    mock_conn = MockConnection()
    try:
        results = execute_screener(sample_dsl, mock_conn)
        print(f"\nResults found: {len(results)}")
        for item in results:
            print(item)
            
        # Save results to file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, "output", "results.json")
        save_results_to_file(results, output_path)
        
    except Exception as e:
        print(f"Execution failed: {e}")
