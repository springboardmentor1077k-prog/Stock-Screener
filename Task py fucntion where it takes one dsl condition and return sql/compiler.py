import json
import os
from typing import Any, Dict, Optional

def compile_condition(field: str, value: Any) -> Optional[str]:
    """
    Compiles a single DSL condition into a SQL WHERE clause fragment.
    
    Args:
        field: The field name from the DSL (e.g., 'peg_ratio_max', 'industry_category').
        value: The value for the condition.
        
    Returns:
        A string containing the SQL fragment, or None if the field is unknown.
    """
    # Sanitize value for SQL string to prevent injection (basic example)
    if isinstance(value, str):
        safe_value = value.replace("'", "''")
        val_str = f"'{safe_value}'"
    else:
        val_str = str(value)

    if field == "industry_category":
        return f"sector = {val_str}"
    
    if field == "peg_ratio_max":
        return f"peg < {val_str}"
    
    if field == "fcf_to_debt_min":
        # Handle division by zero and ensure debt is not zero if we require a ratio
        return f"(CASE WHEN debt = 0 THEN 0 ELSE fcf / debt END) >= {val_str}"
         
    if field == "price_vs_target":
        if value == "<= target_low":
            return "price <= target_low"
        elif value == "<= target_mean":
            return "price <= target_mean"
        else:
            # Default fallback or error
            return "price <= target_low"
            
    if field == "revenue_yoy_positive":
        if value:
            return "rev_yoy > 0"
        return None # or handle false case if needed
        
    if field == "ebitda_yoy_positive":
        if value:
            return "ebitda_yoy > 0"
        return None
        
    if field == "earnings_beat_likely":
        if value:
            # Assuming 'beats' column tracks number of recent beats, and we require >= 3 as per python implementation
            return "beats >= 3"
        return None
        
    if field == "buyback_announced":
        if value:
            return "buyback = TRUE"
        return "buyback = FALSE"
        
    if field == "next_earnings_within_days":
        return f"next_earnings_days <= {val_str}"
        
    return None

def compile_dsl_to_sql(dsl: Dict[str, Any], table_name: str = "stocks") -> str:
    """
    Compiles the full DSL dictionary into a complete SQL query.
    
    Args:
        dsl: The DSL dictionary containing 'industry_category' and 'filters'.
        table_name: The name of the database table.
        
    Returns:
        A complete SQL SELECT statement.
    """
    conditions = []
    
    # Handle top-level fields
    if "industry_category" in dsl:
        cond = compile_condition("industry_category", dsl["industry_category"])
        if cond:
            conditions.append(cond)
            
    # Handle filters
    if "filters" in dsl and isinstance(dsl["filters"], dict):
        for key, val in dsl["filters"].items():
            cond = compile_condition(key, val)
            if cond:
                conditions.append(cond)
                
    where_clause = " AND ".join(conditions)
    
    if where_clause:
        return f"SELECT * FROM {table_name} WHERE {where_clause};"
    else:
        return f"SELECT * FROM {table_name};"

def save_sql_to_file(sql: str, file_path: str):
    """
    Saves the generated SQL string to a file.
    
    Args:
        sql: The SQL query string.
        file_path: The absolute or relative path to the output file.
    """
    # Ensure directory exists
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"SQL query saved to: {os.path.abspath(file_path)}")

if __name__ == "__main__":
    # Define paths
    # Assuming relative path to the project structure based on current location
    # Adjust this path if the script is moved
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    dsl_input_path = os.path.join(project_root, "Task python scripts Structured Market Intelligence LLM Pipeline", "output", "dsl.json")
    output_sql_path = os.path.join(base_dir, "output", "query.sql")

    dsl_data = None
    
    # Try to load DSL from file
    if os.path.exists(dsl_input_path):
        try:
            with open(dsl_input_path, "r", encoding="utf-8") as f:
                dsl_data = json.load(f)
            print(f"Loaded DSL from: {dsl_input_path}")
        except Exception as e:
            print(f"Error loading DSL file: {e}")
    
    # Fallback if file not found or error
    if not dsl_data:
        print("Using default sample DSL.")
        dsl_data = {
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

    # Compile
    sql = compile_dsl_to_sql(dsl_data)
    print("\nGenerated SQL:")
    print(sql)
    
    # Save to file
    save_sql_to_file(sql, output_sql_path)
