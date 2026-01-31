"""
Test suite for DSL parser and mapper integration
"""

import sys
sys.path.insert(0, 'c:/Users/Sabeshhan/Desktop/Stock_Screener/stock-screener/backend')

from app.schemas.dsl import generate_dsl
from app.utils.dsl_mapper import map_dsl_to_screener_query

def test_dsl_parser():
    """Test DSL parser with various queries"""
    
    test_cases = [
        ("pe below 20", "PE < 20"),
        ("roe above 15", "ROE > 15"),
        ("price above 100 and volume greater than 1000000", "Multiple conditions"),
        ("debt to equity below 0.5", "Debt to equity ratio"),
        ("dividend yield above 2", "Dividend yield"),
    ]
    
    print("=" * 60)
    print("DSL PARSER TESTS")
    print("=" * 60)
    
    for query, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: '{query}'")
        result = generate_dsl(query)
        print(f"Output: {result}")
        
        if result.get("status") == "success":
            try:
                conditions = map_dsl_to_screener_query(result)
                print(f"Mapped: {[(c.field, c.operator, c.value) for c in conditions]}")
                print("✓ SUCCESS")
            except Exception as e:
                print(f"✗ MAPPING ERROR: {e}")
        else:
            print(f"✗ PARSING ERROR: {result.get('error')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_dsl_parser()
