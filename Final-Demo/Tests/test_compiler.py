import pytest
import sys
import os

# 1. Setup path to find your backend files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. IMPORT FROM THE CORRECT FILE
from recursive_compiler import compile_dsl_to_sql_with_params

class TestRecursiveCompiler:

    # --- 1. BASIC LOGIC ---

    def test_simple_and(self):
        """Test compiling a simple AND condition."""
        dsl = {
            "logic": "AND",
            "filters": [
                {"field": "pe_ratio", "operator": "<", "value": 20},
                {"field": "peg_ratio", "operator": "<", "value": 1.5}
            ]
        }
        # The function returns a TUPLE: (sql_string, parameter_list)
        sql, params = compile_dsl_to_sql_with_params(dsl)
        
        # Expectation: SQL contains placeholders (%s), params list contains values
        assert "pe_ratio < %s" in sql
        assert "peg_ratio < %s" in sql
        assert "AND" in sql
        assert 20 in params
        assert 1.5 in params

    def test_simple_or(self):
        """Test compiling a simple OR condition."""
        dsl = {
            "logic": "OR",
            "filters": [
                {"field": "sector", "operator": "=", "value": "Technology"},
                {"field": "sector", "operator": "=", "value": "Healthcare"}
            ]
        }
        sql, params = compile_dsl_to_sql_with_params(dsl)
        
        assert "sector = %s" in sql
        assert "OR" in sql
        assert "Technology" in params
        assert "Healthcare" in params

    # --- 2. SPECIAL OPERATORS ---

    def test_between_operator(self):
        """Test the BETWEEN operator conversion."""
        dsl = {
            "logic": "AND",
            "filters": [
                {"field": "pe_ratio", "operator": "between", "value": [10, 20]}
            ]
        }
        sql, params = compile_dsl_to_sql_with_params(dsl)
        
        # Should generate: pe_ratio BETWEEN %s AND %s
        assert "BETWEEN %s AND %s" in sql
        assert 10 in params
        assert 20 in params

    def test_empty_rules(self):
        """Test behavior when no filters are provided."""
        dsl = {"logic": "AND", "filters": []}
        sql, params = compile_dsl_to_sql_with_params(dsl)
        
        # Should return a generic TRUE statement
        assert "1=1" in sql or "TRUE" in sql
