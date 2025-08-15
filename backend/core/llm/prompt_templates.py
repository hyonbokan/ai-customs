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
    "confidence_score": <float between 0-1>,
    "recommendations": [
        "<overall recommendations>"
    ],
    "risk_level": "<low|medium|high>",
    "requires_inspection": <boolean>
}}
"""

        return prompt

    @staticmethod
    def get_pdf_extraction_prompt(extracted_text: str) -> str:
        """
        Generate prompt for extracting structured data from PDF text.
        """
        return f"""
You are an expert document processor. Extract structured customs declaration data from the following PDF text.

PDF Text:
{extracted_text}

Please extract and structure the following information:

1. **Declaration Details**:
   - Declaration number
   - Declaration date
   - Country of origin
   - Destination country

2. **Importer/Exporter Information**:
   - Importer name and address
   - Exporter name and address
   - Contact information

3. **Goods Information**:
   - Product descriptions
   - HS codes
   - Quantities and units
   - Values and currencies
   - Country of origin per item

4. **Additional Information**:
   - Total value
   - Currency
   - Transportation details
   - Any special notes

Return the extracted data in JSON format:
{{
    "declaration_number": "<number>",
    "declaration_date": "<date>",
    "importer": {{
        "name": "<name>",
        "address": "<address>"
    }},
    "exporter": {{
        "name": "<name>",
        "address": "<address>"
    }},
    "goods": [
        {{
            "description": "<description>",
            "hs_code": "<code>",
            "quantity": "<quantity>",
            "unit": "<unit>",
            "value": "<value>",
            "currency": "<currency>",
            "origin": "<country>"
        }}
    ],
    "total_value": "<total>",
    "currency": "<currency>",
    "transportation": "<details>",
    "extraction_confidence": <float between 0-1>
}}
"""
