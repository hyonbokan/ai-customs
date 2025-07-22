from typing import Dict, Any, List, Optional


class DeclarationDataValidator:
    """Helper class for validating customs declaration data."""
    
    REQUIRED_FIELDS = [
        "declaration_number",
        "importer",
        "goods",
        "total_value"
    ]
    
    @staticmethod
    def validate_declaration_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate customs declaration data structure.
        Returns validation result with errors if any.
        """
        errors = []
        warnings = []
        
        # Check required fields
        for field in DeclarationDataValidator.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate data types
        if "total_value" in data:
            try:
                float(data["total_value"])
            except (ValueError, TypeError):
                errors.append("total_value must be a valid number")
        
        # Validate goods structure
        if "goods" in data and isinstance(data["goods"], list):
            for i, good in enumerate(data["goods"]):
                if not isinstance(good, dict):
                    errors.append(f"goods[{i}] must be an object")
                elif "description" not in good:
                    warnings.append(f"goods[{i}] missing description")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def normalize_declaration_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and clean declaration data.
        """
        normalized = data.copy()
        
        # Convert string numbers to floats
        if "total_value" in normalized:
            try:
                normalized["total_value"] = float(normalized["total_value"])
            except (ValueError, TypeError):
                pass
        
        # Normalize text fields
        text_fields = ["importer", "declaration_number"]
        for field in text_fields:
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = normalized[field].strip()
        
        return normalized 