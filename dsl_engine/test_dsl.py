import unittest
import json
from compiler import compile_dsl
from schema import DSL_SCHEMA

class TestDSLCompiler(unittest.TestCase):
    def test_simple_condition(self):
        dsl = {
            "query": {
                "type": "condition",
                "field": "industry_category",
                "value": "Technology"
            }
        }
        sql, params = compile_dsl(dsl)
        self.assertIn("sector = %(sector_1)s", sql)
        self.assertEqual(params["sector_1"], "Technology")

    def test_logical_and(self):
        dsl = {
            "query": {
                "type": "logical",
                "operator": "AND",
                "children": [
                    {
                        "type": "condition",
                        "field": "industry_category",
                        "value": "Technology"
                    },
                    {
                        "type": "condition",
                        "field": "peg_ratio_max",
                        "value": 1.5
                    }
                ]
            }
        }
        sql, params = compile_dsl(dsl)
        self.assertIn("AND", sql)
        self.assertIn("sector = %(sector_1)s", sql)
        self.assertIn("peg < %(peg_2)s", sql)
        self.assertEqual(params["sector_1"], "Technology")
        self.assertEqual(params["peg_2"], 1.5)

    def test_nested_logical(self):
        # (Sector = Tech AND (PEG < 1.5 OR Buyback = True))
        dsl = {
            "query": {
                "type": "logical",
                "operator": "AND",
                "children": [
                    {
                        "type": "condition",
                        "field": "industry_category",
                        "value": "Technology"
                    },
                    {
                        "type": "logical",
                        "operator": "OR",
                        "children": [
                            {
                                "type": "condition",
                                "field": "peg_ratio_max",
                                "value": 1.5
                            },
                            {
                                "type": "condition",
                                "field": "buyback_announced",
                                "value": True
                            }
                        ]
                    }
                ]
            }
        }
        sql, params = compile_dsl(dsl)
        # Expected roughly: (sector = ... AND (peg < ... OR buyback = TRUE))
        # Note: parens depend on implementation detail
        print(f"Nested SQL: {sql}")
        self.assertIn("sector = %(sector_1)s", sql)
        self.assertIn("peg < %(peg_2)s", sql)
        self.assertIn("buyback = TRUE", sql)
        self.assertIn(" OR ", sql)
        self.assertEqual(params["sector_1"], "Technology")
        self.assertEqual(params["peg_2"], 1.5)

    def test_limit(self):
        dsl = {
            "query": {
                "type": "condition",
                "field": "industry_category",
                "value": "Technology"
            },
            "limit": 10
        }
        sql, params = compile_dsl(dsl)
        self.assertIn("LIMIT %(limit_2)s", sql) # limit_2 because sector_1 is first
        self.assertEqual(params["limit_2"], 10)

    def test_empty_query(self):
        dsl = {"query": None}
        sql, params = compile_dsl(dsl)
        self.assertIn("SELECT * FROM stocks", sql)
        self.assertNotIn("WHERE", sql)

    def test_unknown_field_safe(self):
        dsl = {
            "query": {
                "type": "condition",
                "field": "unknown_field",
                "value": "whatever"
            }
        }
        sql, params = compile_dsl(dsl)
        self.assertIn("SELECT * FROM stocks", sql)
        self.assertNotIn("WHERE", sql) # Should ignore unknown field resulting in empty where clause

if __name__ == '__main__':
    unittest.main()
