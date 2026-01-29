import json

DSL_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "definitions": {
        "condition": {
            "type": "object",
            "properties": {
                "type": {"const": "condition"},
                "field": {
                    "type": "string",
                    "enum": [
                        "industry_category",
                        "peg_ratio_max",
                        "fcf_to_debt_min",
                        "price_vs_target",
                        "revenue_yoy_positive",
                        "ebitda_yoy_positive",
                        "earnings_beat_likely",
                        "buyback_announced",
                        "next_earnings_within_days"
                    ]
                },
                "value": {}
            },
            "required": ["type", "field", "value"]
        },
        "logical": {
            "type": "object",
            "properties": {
                "type": {"const": "logical"},
                "operator": {"enum": ["AND", "OR"]},
                "children": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/node"}
                }
            },
            "required": ["type", "operator", "children"]
        },
        "node": {
            "oneOf": [
                {"$ref": "#/definitions/condition"},
                {"$ref": "#/definitions/logical"}
            ]
        }
    },
    "type": "object",
    "properties": {
        "query": {"$ref": "#/definitions/node"},
        "limit": {"type": "integer", "minimum": 1}
    },
    "required": ["query"]
}

def get_schema_json():
    return json.dumps(DSL_SCHEMA, indent=2)
