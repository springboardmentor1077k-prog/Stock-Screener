"""
Enhanced DSL Compiler Components for AI-Powered Stock Screener
Provides granular control and flexibility for DSL to SQL compilation
"""

from enum import Enum
from typing import Dict, Any, List, Tuple
from functools import lru_cache
from backend.models.schemas import Condition, ConditionOperator, FinancialMetric, TimeFrame


class MetricType(Enum):
    """Classification of metric types for different compilation strategies"""
    SNAPSHOT = "snapshot"           # Current point-in-time values (PE, PEG, etc.)
    TIME_SERIES = "time_series"     # Historical/trend data (quarterly financials)
    DERIVED = "derived"             # Calculated metrics (ratios, growth rates)
    BOOLEAN = "boolean"             # True/false indicators


class CompilationStrategy(Enum):
    """Different strategies for compiling DSL to SQL"""
    DIRECT_MAPPING = "direct_mapping"           # Direct field-to-column mapping
    AGGREGATION = "aggregation"                 # Requires aggregation functions
    TIME_BASED = "time_based"                   # Time-series specific logic
    COMPLEX_CALCULATION = "complex_calculation" # Complex formula-based


# Enhanced mapping table with detailed metadata
DSL_TO_DB_MAPPING: List[Dict[str, Any]] = [
    # Snapshot metrics
    {
        "dsl_field": FinancialMetric.PE_RATIO,
        "db_table": "fundamentals",
        "db_column": "pe_ratio",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Price-to-Earnings ratio"
    },
    {
        "dsl_field": FinancialMetric.PEG_RATIO,
        "db_table": "fundamentals",
        "db_column": "peg_ratio",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Price/Earnings-to-Growth ratio"
    },
    {
        "dsl_field": FinancialMetric.EBITDA,
        "db_table": "fundamentals",
        "db_column": "ebitda",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Earnings Before Interest, Taxes, Depreciation, Amortization"
    },
    {
        "dsl_field": FinancialMetric.FREE_CASH_FLOW,
        "db_table": "fundamentals",
        "db_column": "free_cash_flow",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Free cash flow"
    },
    {
        "dsl_field": FinancialMetric.PROMOTER_HOLDING,
        "db_table": "fundamentals",
        "db_column": "promoter_holding",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Percentage of shares held by promoters"
    },
    {
        "dsl_field": FinancialMetric.DEBT_TO_FREE_CASH_FLOW,
        "db_table": "fundamentals",
        "db_column": "debt_to_free_cash_flow",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Debt to free cash flow ratio"
    },
    {
        "dsl_field": FinancialMetric.REVENUE_GROWTH_YOY,
        "db_table": "fundamentals",
        "db_column": "revenue_growth_yoy",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Year-over-year revenue growth"
    },
    {
        "dsl_field": FinancialMetric.EARNINGS_GROWTH_YOY,
        "db_table": "fundamentals",
        "db_column": "earnings_growth_yoy",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Year-over-year earnings growth"
    },
    {
        "dsl_field": FinancialMetric.CURRENT_PRICE,
        "db_table": "fundamentals",
        "db_column": "current_price",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Current market price"
    },
    {
        "dsl_field": FinancialMetric.MARKET_CAP,
        "db_table": "fundamentals",
        "db_column": "market_cap",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Market capitalization"
    },
    {
        "dsl_field": FinancialMetric.EPS,
        "db_table": "fundamentals",
        "db_column": "eps",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Earnings per share"
    },
    {
        "dsl_field": FinancialMetric.BOOK_VALUE,
        "db_table": "fundamentals",
        "db_column": "book_value",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Book value per share"
    },
    {
        "dsl_field": FinancialMetric.ROE,
        "db_table": "fundamentals",
        "db_column": "roe",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Return on equity"
    },
    {
        "dsl_field": FinancialMetric.ROA,
        "db_table": "fundamentals",
        "db_column": "roa",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Return on assets"
    },
    {
        "dsl_field": FinancialMetric.DIVIDEND_YIELD,
        "db_table": "fundamentals",
        "db_column": "dividend_yield",
        "metric_type": MetricType.SNAPSHOT,
        "compilation_strategy": CompilationStrategy.DIRECT_MAPPING,
        "description": "Dividend yield percentage"
    },
    # Time series metrics
    {
        "dsl_field": FinancialMetric.QUARTER_REVENUE,
        "db_table": "quarterly_financials",
        "db_column": "revenue",
        "metric_type": MetricType.TIME_SERIES,
        "compilation_strategy": CompilationStrategy.TIME_BASED,
        "description": "Quarterly revenue"
    },
    {
        "dsl_field": FinancialMetric.QUARTER_EBITDA,
        "db_table": "quarterly_financials",
        "db_column": "ebitda",
        "metric_type": MetricType.TIME_SERIES,
        "compilation_strategy": CompilationStrategy.TIME_BASED,
        "description": "Quarterly EBITDA"
    },
    {
        "dsl_field": FinancialMetric.QUARTER_NET_PROFIT,
        "db_table": "quarterly_financials",
        "db_column": "net_profit",
        "metric_type": MetricType.TIME_SERIES,
        "compilation_strategy": CompilationStrategy.TIME_BASED,
        "description": "Quarterly net profit"
    }
]


# Operator mapping dictionary
OPERATOR_MAP: Dict[ConditionOperator, str] = {
    ConditionOperator.EQUALS: "=",
    ConditionOperator.NOT_EQUALS: "!=",
    ConditionOperator.GREATER_THAN: ">",
    ConditionOperator.LESS_THAN: "<",
    ConditionOperator.GREATER_THAN_OR_EQUAL: ">=",
    ConditionOperator.LESS_THAN_OR_EQUAL: "<=",
    ConditionOperator.BETWEEN: "BETWEEN",
    ConditionOperator.IN: "IN",
    ConditionOperator.CONTAINS: "LIKE",
}


def compile_single_condition_to_sql_fragment(condition: Condition) -> Tuple[str, Dict[str, Any]]:
    """
    Rule compiler function that takes one DSL condition and returns SQL fragment with parameters
    
    Args:
        condition: A single Condition object from the DSL
        
    Returns:
        Tuple of (SQL fragment, parameters dict)
    """
    # Find the mapping for this field using cached function
    field_mapping = get_field_mapping(condition.field.value)
    
    # Get the database column name
    db_column = field_mapping["db_column"]
    
    # Get the SQL operator
    sql_operator = OPERATOR_MAP.get(condition.operator)
    if not sql_operator:
        raise ValueError(f"No SQL operator mapping for: {condition.operator}")
    
    # Generate parameter name based on field and timestamp to avoid conflicts
    import time
    param_suffix = int(time.time() * 1000000) % 1000000  # microsecond precision suffix
    param_name = f"{db_column}_{param_suffix}"
    
    # Build the SQL fragment
    if condition.operator == ConditionOperator.BETWEEN:
        # Handle BETWEEN operator specially
        if not isinstance(condition.value, list) or len(condition.value) != 2:
            raise ValueError("BETWEEN operator requires a list of two values")
        lower_param = f"{param_name}_lower"
        upper_param = f"{param_name}_upper"
        sql_fragment = f"{db_column} BETWEEN :{lower_param} AND :{upper_param}"
        params = {
            lower_param: condition.value[0],
            upper_param: condition.value[1]
        }
    else:
        sql_fragment = f"{db_column} {sql_operator} :{param_name}"
        params = {param_name: condition.value}
    
    return sql_fragment, params


@lru_cache(maxsize=128)
def get_field_mapping(field_name: str) -> Dict[str, Any]:
    """
    Helper function to retrieve field mapping information
    
    Args:
        field_name: The name of the DSL field to look up
        
    Returns:
        Dictionary containing the field mapping information
    """
    for mapping in DSL_TO_DB_MAPPING:
        if mapping["dsl_field"].value == field_name:
            return mapping
    
    raise ValueError(f"No mapping found for field: {field_name}")


def get_compilation_strategy(field_name: str) -> CompilationStrategy:
    """
    Get the compilation strategy for a specific field
    
    Args:
        field_name: The name of the DSL field
        
    Returns:
        CompilationStrategy enum value
    """
    mapping = get_field_mapping(field_name)
    return mapping["compilation_strategy"]


def get_metric_type(field_name: str) -> MetricType:
    """
    Get the metric type for a specific field
    
    Args:
        field_name: The name of the DSL field
        
    Returns:
        MetricType enum value
    """
    mapping = get_field_mapping(field_name)
    return mapping["metric_type"]


def validate_condition(condition: Condition) -> bool:
    """
    Validate a condition based on its metric type and compilation strategy
    
    Args:
        condition: The condition to validate
        
    Returns:
        Boolean indicating if the condition is valid
    """
    try:
        mapping = get_field_mapping(condition.field.value)
        
        # Additional validation based on metric type
        if mapping["metric_type"] == MetricType.SNAPSHOT:
            # Snapshot metrics should have numeric values
            if not isinstance(condition.value, (int, float)):
                return False
        
        # Validate operator compatibility with metric type
        if condition.operator == ConditionOperator.CONTAINS:
            # CONTAINS operator may not be appropriate for numeric metrics
            if mapping["metric_type"] in [MetricType.SNAPSHOT, MetricType.TIME_SERIES]:
                # For numeric fields, CONTAINS doesn't make sense
                pass  # Allow it but in real implementation you might want to validate further
        
        return True
    except ValueError:
        from ..core.exceptions import ValidationException
        raise ValidationException(detail=f"Invalid field mapping: {condition.field.value}")


# Example usage and testing
if __name__ == "__main__":
    # Example of using the enhanced components
    from backend.models.schemas import FinancialMetric, ConditionOperator
    
    # Create a sample condition
    sample_condition = Condition(
        field=FinancialMetric.PE_RATIO,
        operator=ConditionOperator.LESS_THAN,
        value=15.0
    )
    
    # Compile to SQL fragment
    sql_fragment, params = compile_single_condition_to_sql_fragment(sample_condition)
    print(f"Condition: PE Ratio < 15")
    print(f"SQL Fragment: {sql_fragment}")
    print(f"Parameters: {params}")
    print()
    
    # Get field mapping information
    pe_mapping = get_field_mapping("pe_ratio")
    print(f"PE Ratio Mapping: {pe_mapping}")
    print()
    
    # Get metric type and compilation strategy
    metric_type = get_metric_type("pe_ratio")
    comp_strategy = get_compilation_strategy("pe_ratio")
    print(f"PE Ratio - Metric Type: {metric_type}, Strategy: {comp_strategy}")
    
    # Validate condition
    is_valid = validate_condition(sample_condition)
    print(f"Condition Valid: {is_valid}")