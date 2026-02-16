# Screener Engine Service
from typing import List, Dict, Any
from backend.models.schemas import ScreenerDSL, ConditionOperator
from sqlalchemy import text
from ..core.cache import TTLCache
import json
import hashlib


class ScreenerEngineService:
    def __init__(self):
        # Map DSL operators to SQL operators
        self.operator_map = {
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
        
        # Valid financial metric fields to prevent SQL injection
        self.valid_fields = {
            "pe_ratio", "peg_ratio", "ebitda", "free_cash_flow", "promoter_holding",
            "debt_to_free_cash_flow", "revenue_growth_yoy", "ebitda_growth_yoy",
            "earnings_growth_yoy", "current_price", "market_cap", "eps", "book_value",
            "roe", "roa", "dividend_yield"
        }

        # Simple in-process cache for compiled SQL + params per DSL
        # This avoids recompiling the same screener query repeatedly.
        self._compile_cache = TTLCache(ttl_seconds=600, max_items=256)
    
    def _dsl_cache_key(self, dsl: ScreenerDSL) -> str:
        """
        Create a stable cache key for a ScreenerDSL by hashing its JSON representation.
        """
        # Use the Pydantic model's json() representation for stability.
        payload = dsl.model_dump(mode="json")
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def compile_to_sql(self, dsl: ScreenerDSL) -> str:
        """Compile DSL to safe SQL query"""
        # Start building the SQL query
        sql = "SELECT ms.symbol, ms.company_name, ms.exchange, "
        sql += "f.pe_ratio, f.peg_ratio, f.ebitda, f.free_cash_flow, f.promoter_holding, "
        sql += "f.debt_to_free_cash_flow, f.revenue_growth_yoy, f.ebitda_growth_yoy, "
        sql += "f.earnings_growth_yoy, f.current_price, f.market_cap, f.eps, f.book_value, "
        sql += "f.roe, f.roa, f.dividend_yield "
        sql += "FROM master_stocks ms "
        sql += "JOIN fundamentals f ON ms.stock_id = f.stock_id "
        
        # Add conditions
        where_conditions = []
        
        # Process each rule
        for rule in dsl.rules:
            rule_conditions = []

            for condition in rule.conditions:
                field = condition.field.value
                operator = condition.operator
                value = condition.value

                # Validate field to prevent SQL injection
                if field not in self.valid_fields:
                    raise ValueError(f"Invalid field: {field}")

                # Map operator
                sql_operator = self.operator_map.get(operator)
                if sql_operator is None:
                    raise ValueError(f"Invalid operator: {operator}")

                # Build condition
                condition_sql = f"{field} {sql_operator} :{field}"
                rule_conditions.append(condition_sql)

            # Combine conditions within the rule with its logical operator (AND/OR)
            if rule_conditions:
                logical = (rule.logical_operator or "AND").upper()
                joiner = f" {logical} "
                rule_condition = f"({joiner.join(rule_conditions)})"
                where_conditions.append(rule_condition)
        
        # Add exchange filter if specified
        if dsl.exchanges:
            exchange_list = [exchange.value for exchange in dsl.exchanges]
            exchange_placeholders = ", ".join([f":exchange_{i}" for i in range(len(exchange_list))])
            exchange_condition = f"ms.exchange IN ({exchange_placeholders})"
            where_conditions.append(exchange_condition)
        
        # Add sector filter if specified
        if dsl.sectors:
            sector_placeholders = ", ".join([f":sector_{i}" for i in range(len(dsl.sectors))])
            sector_condition = f"ms.sector IN ({sector_placeholders})"
            where_conditions.append(sector_condition)
        
        # Add industry filter if specified
        if dsl.industries:
            industry_placeholders = ", ".join([f":industry_{i}" for i in range(len(dsl.industries))])
            industry_condition = f"ms.industry IN ({industry_placeholders})"
            where_conditions.append(industry_condition)
        
        # Combine all conditions with AND
        if where_conditions:
            sql += "WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY
        sql += " ORDER BY f.current_price DESC"
        
        return sql
    
    def compile_to_sql_with_params(self, dsl: ScreenerDSL) -> tuple[str, dict]:
        """
        Compile DSL to safe SQL query with parameters.
        Results are cached per distinct DSL to avoid repeated work.
        """
        cache_key = self._dsl_cache_key(dsl)
        cached = self._compile_cache.get(cache_key)
        if cached is not None:
            return cached
        # Start building the SQL query
        sql = "SELECT ms.symbol, ms.company_name, ms.exchange, "
        sql += "f.pe_ratio, f.peg_ratio, f.ebitda, f.free_cash_flow, f.promoter_holding, "
        sql += "f.debt_to_free_cash_flow, f.revenue_growth_yoy, f.ebitda_growth_yoy, "
        sql += "f.earnings_growth_yoy, f.current_price, f.market_cap, f.eps, f.book_value, "
        sql += "f.roe, f.roa, f.dividend_yield "
        sql += "FROM master_stocks ms "
        sql += "JOIN fundamentals f ON ms.stock_id = f.stock_id "
        
        # Add conditions
        where_conditions = []
        params = {}
        
        # Process each rule
        for rule_idx, rule in enumerate(dsl.rules):
            rule_conditions = []

            for condition_idx, condition in enumerate(rule.conditions):
                field = condition.field.value
                operator = condition.operator
                value = condition.value

                # Validate field to prevent SQL injection
                if field not in self.valid_fields:
                    raise ValueError(f"Invalid field: {field}")

                # Map operator
                sql_operator = self.operator_map.get(operator)
                if sql_operator is None:
                    raise ValueError(f"Invalid operator: {operator}")

                # Create parameter name
                param_name = f"{field}_{rule_idx}_{condition_idx}"

                # Handle BETWEEN operator specially
                if operator == ConditionOperator.BETWEEN:
                    if not isinstance(value, list) or len(value) != 2:
                        raise ValueError("BETWEEN operator requires a list of two values")
                    lower_param = f"{param_name}_lower"
                    upper_param = f"{param_name}_upper"
                    condition_sql = f"{field} BETWEEN :{lower_param} AND :{upper_param}"
                    params[lower_param] = value[0]
                    params[upper_param] = value[1]
                else:
                    condition_sql = f"{field} {sql_operator} :{param_name}"
                    params[param_name] = value

                rule_conditions.append(condition_sql)

            # Combine conditions within the rule with its logical operator (AND/OR)
            if rule_conditions:
                logical = (rule.logical_operator or "AND").upper()
                joiner = f" {logical} "
                rule_condition = f"({joiner.join(rule_conditions)})"
                where_conditions.append(rule_condition)
        
        # Add exchange filter if specified
        if dsl.exchanges:
            exchange_list = [exchange.value for exchange in dsl.exchanges]
            for i, exchange_val in enumerate(exchange_list):
                param_name = f"exchange_{i}"
                params[param_name] = exchange_val
            exchange_placeholders = ", ".join([f":exchange_{i}" for i in range(len(exchange_list))])
            exchange_condition = f"ms.exchange IN ({exchange_placeholders})"
            where_conditions.append(exchange_condition)
        
        # Add sector filter if specified
        if dsl.sectors:
            for i, sector in enumerate(dsl.sectors):
                param_name = f"sector_{i}"
                params[param_name] = sector
            sector_placeholders = ", ".join([f":sector_{i}" for i in range(len(dsl.sectors))])
            sector_condition = f"ms.sector IN ({sector_placeholders})"
            where_conditions.append(sector_condition)
        
        # Add industry filter if specified
        if dsl.industries:
            for i, industry in enumerate(dsl.industries):
                param_name = f"industry_{i}"
                params[param_name] = industry
            industry_placeholders = ", ".join([f":industry_{i}" for i in range(len(dsl.industries))])
            industry_condition = f"ms.industry IN ({industry_placeholders})"
            where_conditions.append(industry_condition)
        
        # Combine all conditions with AND
        if where_conditions:
            sql += "WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY
        sql += " ORDER BY f.current_price DESC"
        
        result = (sql, params)
        self._compile_cache.set(cache_key, result)
        return result
    
    def validate_dsl(self, dsl: ScreenerDSL) -> str:
        """Validate the DSL structure"""
        if not dsl.rules:
            return "DSL must contain at least one rule"
        
        for i, rule in enumerate(dsl.rules):
            if not rule.conditions:
                return f"Rule {i} must contain at least one condition"
            
            for j, condition in enumerate(rule.conditions):
                if not condition.field:
                    return f"Condition {j} in rule {i} must have a field"
                
                if condition.field.value not in self.valid_fields:
                    return f"Invalid field in condition {j} in rule {i}: {condition.field.value}"
                
                if not condition.operator:
                    return f"Condition {j} in rule {i} must have an operator"
                
                if condition.value is None:
                    return f"Condition {j} in rule {i} must have a value"
        
        return None  # No validation errors
    
    def execute_screener(self, dsl: ScreenerDSL, db_session):
        """Execute the screener query"""
        # Validate the DSL first
        validation_error = self.validate_dsl(dsl)
        if validation_error:
            raise ValueError(validation_error)
        
        # Compile to SQL and parameters
        sql, params = self.compile_to_sql_with_params(dsl)
        
        # Execute the query with parameters
        result = db_session.execute(text(sql), params)
        rows = result.fetchall()
        
        # Convert to list of dictionaries
        columns = result.keys()
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        return results
    
    # Enhanced functionality using the new DSL compiler
    def compile_single_condition_demo(self, condition):
        """
        Demonstration method showing integration with enhanced DSL compiler
        This method showcases the granular control and flexibility of the new component
        """
        try:
            from .dsl_compiler import compile_single_condition_to_sql_fragment, validate_condition
            
            # Validate the condition first
            if not validate_condition(condition):
                raise ValueError("Invalid condition")
            
            # Compile to SQL fragment using the enhanced compiler
            sql_fragment, params = compile_single_condition_to_sql_fragment(condition)
            
            return {
                "sql_fragment": sql_fragment,
                "parameters": params,
                "message": "Successfully compiled using enhanced DSL compiler"
            }
        except ImportError:
            # Fallback if the enhanced compiler is not available
            return {
                "sql_fragment": f"{condition.field.value} {self.operator_map.get(condition.operator)} :{condition.field.value}",
                "parameters": {condition.field.value: condition.value},
                "message": "Using basic compiler (enhanced compiler not available)"
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": "Compilation failed"
            }