"""
Unit tests for rule compiler: snapshot, time-series, nested grouping.
"""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "dsl_engine"))
sys.path.append(os.path.join(PROJECT_ROOT, "Dynamic_SQL_Screener_Engine"))

from compiler import DSLCompiler
from screener import compile_dsl_to_sql

class TestRuleCompiler:
    def test_snapshot_rules_compile(self):
        # Arrange
        dsl = {
            "query": {
                "type": "logical",
                "operator": "AND",
                "children": [
                    {"type": "condition", "field": "industry_category", "value": "Technology"},
                    {"type": "condition", "field": "peg_ratio_max", "value": 2.0},
                ],
            }
        }
        # Act
        sql, params = DSLCompiler().compile(dsl)
        # Assert
        assert "SELECT * FROM stocks WHERE" in sql
        assert "sector = %(sector_1)s" in sql
        assert "peg < %(peg_2)s" in sql
        assert params["sector_1"] == "Technology"
        assert params["peg_2"] == 2.0

    def test_time_series_limit_last_n(self):
        # Arrange
        dsl = {"industry_category": "Technology", "last_n_quarters": 3}
        # Act
        sql, params = compile_dsl_to_sql(dsl)
        # Assert
        assert "LIMIT %(limit_n)s" in sql
        assert params["limit_n"] == 3

    def test_nested_and_or_grouping(self):
        # Arrange
        dsl = {
            "query": {
                "type": "logical",
                "operator": "AND",
                "children": [
                    {"type": "condition", "field": "industry_category", "value": "Information Technology"},
                    {
                        "type": "logical",
                        "operator": "OR",
                        "children": [
                            {"type": "condition", "field": "buyback_announced", "value": True},
                            {"type": "condition", "field": "revenue_yoy_positive", "value": True},
                        ],
                    },
                ],
            }
        }
        # Act
        sql, params = DSLCompiler().compile(dsl)
        # Assert
        assert "(" in sql and ")" in sql
        assert " AND " in sql and " OR " in sql
        assert "buyback = TRUE" in sql
        assert "rev_yoy > 0" in sql
