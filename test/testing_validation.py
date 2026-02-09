"""
Unit tests for DSL validation (AAA pattern).
"""
import sys
import os
import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "dsl_engine"))

from validator import validate_dsl

class TestDSLValidationInvalidCases:
    def test_unsupported_field(self):
        # Arrange
        dsl = {"query": {"type": "condition", "field": "unknown_metric", "value": 10}}
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert not valid
        assert "Unsupported field" in msg

    def test_wrong_operator_in_logical(self):
        # Arrange
        dsl = {
            "query": {
                "type": "logical",
                "operator": "XOR",
                "children": [
                    {"type": "condition", "field": "peg_ratio_max", "value": 1.2},
                    {"type": "condition", "field": "revenue_yoy_positive", "value": True},
                ],
            }
        }
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert not valid
        assert "Wrong operator" in msg

    def test_malformed_dsl_missing_type(self):
        # Arrange
        dsl = {"query": {"field": "peg_ratio_max", "value": 1.2}}
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert not valid
        assert "Malformed DSL" in msg

    def test_invalid_last_n_value(self):
        # Arrange
        dsl = {
            "query": {"type": "condition", "field": "peg_ratio_max", "value": 1.2},
            "last_n_quarters": 0,
        }
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert not valid
        assert "Invalid last_n_quarters" in msg

    def test_missing_required_fields(self):
        # Arrange
        dsl = {"query": {"type": "condition", "field": "peg_ratio_max"}}
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert not valid
        assert "Condition missing required fields" in msg

class TestDSLValidationValidCases:
    def test_valid_condition(self):
        # Arrange
        dsl = {"query": {"type": "condition", "field": "industry_category", "value": "Technology"}}
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert valid
        assert msg == ""

    def test_valid_nested_and_or(self):
        # Arrange
        dsl = {
            "query": {
                "type": "logical",
                "operator": "AND",
                "children": [
                    {"type": "condition", "field": "industry_category", "value": "Technology"},
                    {
                        "type": "logical",
                        "operator": "OR",
                        "children": [
                            {"type": "condition", "field": "peg_ratio_max", "value": 1.5},
                            {"type": "condition", "field": "buyback_announced", "value": True},
                        ],
                    },
                ],
            },
            "last_n_quarters": 4,
        }
        # Act
        valid, msg = validate_dsl(dsl)
        # Assert
        assert valid
        assert msg == ""
