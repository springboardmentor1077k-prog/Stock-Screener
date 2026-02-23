ALLOWED_FIELDS = ["pe_ratio", "peg_ratio", "promoter_holding"]

def validate_conditions(conditions):
    for condition in conditions:
        if condition.field not in ALLOWED_FIELDS:
            raise ValueError(f"Field {condition.field} not allowed")