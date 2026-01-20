import unittest
from compiler import compile_condition, compile_dsl_to_sql

class TestCompiler(unittest.TestCase):
    def test_compile_condition(self):
        self.assertEqual(compile_condition("industry_category", "Technology"), "sector = 'Technology'")
        self.assertEqual(compile_condition("peg_ratio_max", 3.0), "peg < 3.0")
        self.assertEqual(compile_condition("fcf_to_debt_min", 0.25), "(CASE WHEN debt = 0 THEN 0 ELSE fcf / debt END) >= 0.25")
        self.assertEqual(compile_condition("price_vs_target", "<= target_low"), "price <= target_low")
        self.assertEqual(compile_condition("revenue_yoy_positive", True), "rev_yoy > 0")
        self.assertEqual(compile_condition("earnings_beat_likely", True), "beats >= 3")
        self.assertEqual(compile_condition("next_earnings_within_days", 30), "next_earnings_days <= 30")

    def test_compile_dsl_to_sql(self):
        dsl = {
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
        
        expected_sql = (
            "SELECT * FROM stocks WHERE "
            "sector = 'Information Technology' AND "
            "peg < 3.0 AND "
            "(CASE WHEN debt = 0 THEN 0 ELSE fcf / debt END) >= 0.25 AND "
            "price <= target_low AND "
            "rev_yoy > 0 AND "
            "ebitda_yoy > 0 AND "
            "beats >= 3 AND "
            "buyback = TRUE AND "
            "next_earnings_days <= 30;"
        )
        
        generated_sql = compile_dsl_to_sql(dsl)
        print(f"\nGenerated SQL: {generated_sql}")
        self.assertEqual(generated_sql, expected_sql)

if __name__ == '__main__':
    unittest.main()
