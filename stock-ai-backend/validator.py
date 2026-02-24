from field_registry import FIELD_REGISTRY
from error_handlers import ValidationError, validate_not_empty

ALLOWED_OPERATORS = {"<", ">", "=", "<=", ">="}
LOGICAL_OPERATORS = {"AND", "OR"}
MAX_DSL_DEPTH = 5  # Prevent overly complex nested queries


def map_field_name(field):
    """
    Maps dotted field names (e.g., 'fundamentals.pe_ratio') to registry keys (e.g., 'pe_ratio').
    """
    # If field contains a dot, extract the actual field name
    if "." in field:
        return field.split(".")[-1]
    return field


def validate_dsl(dsl):
    """
    Validates the root DSL structure with comprehensive error checking.
    
    Checks for:
    - Empty or None DSL
    - Invalid query indicators
    - Nested depth limits
    - Valid node structure
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check for None or empty DSL
    if dsl is None:
        raise ValidationError(
            "Query DSL is empty",
            details="Please provide a valid screening query"
        )
    
    if not isinstance(dsl, dict):
        raise ValidationError(
            "Invalid query format",
            details="Query must be a valid JSON structure"
        )
    
    # Handle unsupported queries
    if dsl.get("invalid") is True:
        error_msg = dsl.get("error", "Invalid or unsupported query")
        raise ValidationError(
            "Query not supported",
            details=error_msg
        )
    
    # Check if DSL is effectively empty
    if not dsl or (dsl.get("type") is None and dsl.get("invalid") is None):
        raise ValidationError(
            "Query cannot be empty",
            details="Please enter a valid screening query like 'PE ratio less than 25'"
        )
    
    # Validate node structure and depth
    return validate_node(dsl, depth=0)


def validate_node(node, depth=0):
    """
    Recursively validates a DSL node with depth tracking.
    
    Args:
        node: DSL node to validate
        depth: Current depth in the tree (for limiting nesting)
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Check depth limit
    if depth > MAX_DSL_DEPTH:
        raise ValidationError(
            f"Query is too complex (max depth: {MAX_DSL_DEPTH})",
            details="Please simplify your query by reducing nesting levels"
        )
    
    # Check for missing type
    node_type = node.get("type")
    if not node_type:
        return False, "Invalid query structure: missing node type"

    # ---------- CONDITION NODE ----------
    if node_type == "condition":
        field = node.get("field")
        operator = node.get("operator")
        value = node.get("value")

        # Validate field exists
        if not field:
            return False, "Missing field in condition"
        
        # Map dotted field names to registry keys
        field_name = map_field_name(field)

        if field_name not in FIELD_REGISTRY:
            raise ValidationError(
                f"Unsupported metric: '{field}'",
                details=f"Available metrics: {', '.join(list(FIELD_REGISTRY.keys())[:10])}..."
            )

        if operator not in ALLOWED_OPERATORS:
            raise ValidationError(
                f"Invalid operator: '{operator}'",
                details=f"Allowed operators: {', '.join(ALLOWED_OPERATORS)}"
            )

        if value is None:
            return False, f"Missing value for field: {field}"

        return True, "Valid condition"

    # ---------- LOGICAL NODE (AND/OR) ----------
    elif node_type == "logical":
        logic_op = node.get("operator")
        # Support both 'children' and 'conditions' keys
        conditions = node.get("children") or node.get("conditions", [])

        if logic_op not in LOGICAL_OPERATORS:
            return False, f"Unsupported logical operator: {logic_op}"

        if not conditions or len(conditions) < 1:
            return False, f"{logic_op} must have at least one condition"
        
        # If only one child, unwrap and validate it directly
        if len(conditions) == 1:
            return validate_node(conditions[0], depth + 1)

        # Multiple children - validate all
        for i, cond in enumerate(conditions):
            valid, msg = validate_node(cond, depth + 1)
            if not valid:
                return False, f"Invalid condition #{i+1}: {msg}"

        return True, "Valid logical expression"

    # ---------- UNKNOWN NODE TYPE ----------
    else:
        return False, f"Unknown node type: {node_type}"
