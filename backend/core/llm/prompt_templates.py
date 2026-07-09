from typing import Any, Dict, Optional


class PromptTemplates:
    """Templates for LLM prompts."""

    @staticmethod
    def get_customs_analysis_prompt(
        declaration_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate prompt for customs declaration analysis.
        """
        prompt = f"""
You are an expert customs analyst. Analyze the following customs declaration for potential discrepancies, fraud indicators, and compliance issues.

Declaration Data:
{declaration_data}
"""

        if reference_data:
            prompt += f"""
Reference Data (for comparison):
{reference_data}
"""

        prompt += """
Please analyze and identify any discrepancies, inconsistencies, or potential issues in:

1. **Value Assessment**:
   - Declared values vs. expected market prices
   - Currency inconsistencies
   - Unusually low/high valuations

2. **Product Classification**:
   - Product descriptions vs. HS codes
   - Tariff classification accuracy
   - Product origin verification

3. **Quantity & Units**:
   - Quantity and unit inconsistencies
   - Weight vs. volume discrepancies
   - Package count validation

4. **Documentation**:
   - Missing required information
   - Inconsistent supplier/buyer details
   - Suspicious patterns

5. **Compliance Issues**:
   - Restricted/prohibited goods
   - License requirements
   - Country-specific regulations

Return your analysis in the following JSON format:
{{
    "discrepancies_found": <number>,
    "issues": [
        {{
            "category": "<category>",
            "severity": "<low|medium|high>",
            "description": "<detailed description>",
            "recommendation": "<specific action>"
        }}
    ],
    "recommendations": [
        "<overall recommendations>"
    ],
    "risk_level": "<low|medium|high>",
    "requires_inspection": <boolean>
}}
"""

        return prompt
