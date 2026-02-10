import pytest
import sys
import os

# Add the parent directory to sys.path so we can import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_service import nl_to_dsl

class TestDSLValidation:

    # --- HAPPY PATH (VALID CASES) ---
    
    def test_valid_simple_query(self):
        """Case 1: Standard simple query should parse correctly."""
        query = "PE < 20"
        dsl = nl_to_dsl(query)
        
        # Expectation: 1 filter, correct field/op/value
        assert dsl["logic"] == "AND"
        assert len(dsl["filters"]) == 1
        assert dsl["filters"][0]["field"] == "pe_ratio"
        assert dsl["filters"][0]["operator"] == "<"
        assert dsl["filters"][0]["value"] == 20.0

    def test_valid_complex_query(self):
        """Case 2: Complex query with multiple conditions."""
        query = "Technology stocks with PE between 15 and 25 and PEG < 1.5"
        dsl = nl_to_dsl(query)
        
        # Expectation: multiple filters
        assert len(dsl["filters"]) >= 2
        
        # Check specific filters exist
        fields = [f["field"] for f in dsl["filters"]]
        assert "sector" in fields
        assert "pe_ratio" in fields
        assert "peg_ratio" in fields

    # --- EDGE CASES (INVALID INPUTS) ---

    def test_invalid_unsupported_field(self):
        """Case 3: Unsupported fields (e.g., 'Turnover') should be ignored or fallback."""
        query = "Stocks with Turnover > 5000"
        dsl = nl_to_dsl(query)
        
        # Should fallback to default (Technology sector) or ignore the bad field
        fields = [f["field"] for f in dsl["filters"]]
        assert "turnover" not in fields
        
        # Should default to safe fallback (Sector=Technology)
        if len(dsl["filters"]) > 0:
            assert dsl["filters"][0]["field"] == "sector"

    def test_invalid_value_type(self):
        """Case 4: Numeric fields with text values."""
        query = "PE < 'High'"
        dsl = nl_to_dsl(query)
        
        # Regex expects digits (\d+), so 'High' should be ignored.
        # Result should be the fallback (Tech sector)
        assert dsl["filters"][0]["value"] != "High"

    def test_empty_query(self):
        """Case 5: Empty string input."""
        query = ""
        dsl = nl_to_dsl(query)
        
        # Should return a valid default DSL (safe fallback)
        assert dsl["logic"] == "AND"
        assert len(dsl["filters"]) > 0
        assert dsl["filters"][0]["field"] == "sector"