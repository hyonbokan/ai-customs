from typing import Any, Dict

from api.routers.declaration_analyzer.schema import ValidationResult


def validate_declaration_data(data: Dict[str, Any]) -> ValidationResult:
    """
    Validate customs declaration data structure and lightly normalize it.
    Returns a ValidationResult with any errors found.
    """
    errors = []
    required_fields = ["declaration_number", "importer", "goods", "total_value"]

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if "total_value" in data:
        try:
            data["total_value"] = float(data["total_value"])
        except (ValueError, TypeError):
            errors.append("total_value must be a valid number")

    if "goods" in data:
        if not isinstance(data["goods"], list):
            errors.append("goods must be a list")
        else:
            for i, good in enumerate(data["goods"]):
                if not isinstance(good, dict):
                    errors.append(f"goods[{i}] must be an object")
                elif "description" not in good:
                    errors.append(f"goods[{i}] missing description")

    # Simple normalization
    text_fields = ["importer", "declaration_number"]
    for field in text_fields:
        if field in data and isinstance(data[field], str):
            data[field] = data[field].strip()

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        normalized_data=data if is_valid else None,
    )
