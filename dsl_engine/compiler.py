from typing import Any, Dict, Tuple, Optional, List

class DSLCompiler:
    def __init__(self):
        self.param_counter = 0
        self.params = {}

    def _get_unique_param_name(self, base_name: str) -> str:
        self.param_counter += 1
        return f"{base_name}_{self.param_counter}"

    def compile(self, dsl: Dict[str, Any], table_name: str = "stocks") -> Tuple[str, Dict[str, Any]]:
        """
        Compiles a DSL dictionary into a SQL query and parameters.
        
        Args:
            dsl: The DSL dictionary containing 'query' and optional 'limit'.
            table_name: The database table name.
            
        Returns:
            A tuple of (sql_string, parameters_dict).
        """
        self.params = {}
        self.param_counter = 0
        
        query_node = dsl.get("query")
        if not query_node:
            # If no query node, return basic select (or handle limit)
            sql = f"SELECT * FROM {table_name}"
        else:
            where_clause = self._compile_node(query_node)
            if where_clause:
                sql = f"SELECT * FROM {table_name} WHERE {where_clause}"
            else:
                sql = f"SELECT * FROM {table_name}"
        
        limit = dsl.get("limit")
        if limit is not None:
            limit_param = self._get_unique_param_name("limit")
            self.params[limit_param] = limit
            sql += f" LIMIT %({limit_param})s"
            
        sql += ";"
        return sql, self.params

    def _compile_node(self, node: Dict[str, Any]) -> str:
        if not node:
            return ""
            
        node_type = node.get("type")
        if node_type == "logical":
            return self._compile_logical(node)
        elif node_type == "condition":
            return self._compile_condition(node)
        else:
            # Unknown node type, ignore or raise. Ignoring for robustness.
            return ""

    def _compile_logical(self, node: Dict[str, Any]) -> str:
        operator = node.get("operator", "AND")
        children = node.get("children", [])
        
        child_clauses = []
        for child in children:
            clause = self._compile_node(child)
            if clause:
                child_clauses.append(clause)
        
        if not child_clauses:
            return ""
            
        if len(child_clauses) == 1:
            return child_clauses[0]
            
        joined = f" {operator} ".join(child_clauses)
        return f"({joined})"

    def _compile_condition(self, node: Dict[str, Any]) -> str:
        field = node.get("field")
        value = node.get("value")
        
        if field == "industry_category":
            p = self._get_unique_param_name("sector")
            self.params[p] = value
            return f"sector = %({p})s"
            
        if field == "peg_ratio_max":
            p = self._get_unique_param_name("peg")
            self.params[p] = value
            return f"peg < %({p})s"
            
        if field == "fcf_to_debt_min":
            p = self._get_unique_param_name("fcf_debt")
            self.params[p] = value
            return f"(CASE WHEN debt = 0 THEN 0 ELSE fcf / debt END) >= %({p})s"
            
        if field == "price_vs_target":
            if value == "<= target_low":
                return "price <= target_low"
            elif value == "<= target_mean":
                return "price <= target_mean"
            return "price <= target_low"
            
        if field == "revenue_yoy_positive":
            return "rev_yoy > 0" if value else ""
            
        if field == "ebitda_yoy_positive":
            return "ebitda_yoy > 0" if value else ""
            
        if field == "earnings_beat_likely":
            return "beats >= 3" if value else ""
            
        if field == "buyback_announced":
            return "buyback = TRUE" if value else "buyback = FALSE"
            
        if field == "next_earnings_within_days":
            p = self._get_unique_param_name("days")
            self.params[p] = value
            return f"next_earnings_days <= %({p})s"
            
        return ""

def compile_dsl(dsl: Dict[str, Any], table_name: str = "stocks") -> Tuple[str, Dict[str, Any]]:
    """Helper function to compile DSL using a fresh compiler instance."""
    compiler = DSLCompiler()
    return compiler.compile(dsl, table_name)
