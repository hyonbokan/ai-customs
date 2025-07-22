"""
Enhanced Pipeline Prompts for Customs Analysis Workflow.

This module contains all prompts used in the complete customs analysis pipeline
from PDF parsing to LLM analysis to final report generation.
"""

from typing import Dict, Any, Optional, List


class PipelinePrompts:
    """Comprehensive prompts for the customs analysis pipeline."""
    
    @staticmethod
    def get_field_extraction_prompt(clean_content: str, document_type: str = "customs_declaration") -> str:
        """
        Generate prompt for intelligent field extraction from clean PDF content.
        
        This prompt is designed to work with the clean content from Docling PDF parser
        without relying on regex patterns or hardcoded formats.
        """
        return f"""
You are an expert customs document processor with deep knowledge of international trade documentation. 
Extract structured information from the following {document_type} content.

The content has been cleanly extracted from a PDF document and may contain:
- Text content with various layouts
- Table data with structured information
- Mixed languages and formats
- Various document orientations

DOCUMENT CONTENT:
{clean_content}

EXTRACTION REQUIREMENTS:
Please extract and structure ALL relevant information, adapting to the actual content format.
Be intelligent about finding information regardless of layout, language, or document structure.

Extract the following information (if present):

1. **Document Identification**:
   - Document type (invoice, declaration, certificate, etc.)
   - Document number/reference
   - Issue date
   - Validity period (if applicable)

2. **Parties Information**:
   - Seller/Exporter details (name, address, contact)
   - Buyer/Importer details (name, address, contact)
   - Consignee (if different from buyer)
   - Shipping agent/forwarder

3. **Goods Information**:
   - Product descriptions (be detailed)
   - HS codes (Harmonized System codes)
   - Quantities and units of measure
   - Unit prices and total values
   - Currency used
   - Country of origin/manufacture
   - Brand names and model numbers

4. **Trade Terms**:
   - Incoterms (FOB, CIF, etc.)
   - Payment terms
   - Delivery terms
   - Port of loading/discharge

5. **Values and Costs**:
   - Total invoice value
   - Currency
   - Freight costs
   - Insurance costs
   - Other charges

6. **Additional Information**:
   - Certificates (origin, quality, etc.)
   - Special notes or conditions
   - Regulatory information
   - Transportation details

IMPORTANT GUIDELINES:
- Extract information as found, don't make assumptions
- Handle multiple languages intelligently
- Adapt to different document formats and layouts
- Include confidence levels for uncertain extractions
- Preserve original text for critical fields

Return the extracted data in this JSON format:
{{
    "document_info": {{
        "type": "<document_type>",
        "number": "<document_number>",
        "date": "<issue_date>",
        "validity": "<validity_period>"
    }},
    "parties": {{
        "seller": {{
            "name": "<seller_name>",
            "address": "<seller_address>",
            "contact": "<contact_info>",
            "country": "<country>"
        }},
        "buyer": {{
            "name": "<buyer_name>",
            "address": "<buyer_address>",
            "contact": "<contact_info>",
            "country": "<country>"
        }},
        "consignee": {{
            "name": "<consignee_name>",
            "address": "<consignee_address>",
            "country": "<country>"
        }}
    }},
    "goods": [
        {{
            "description": "<detailed_description>",
            "hs_code": "<hs_code>",
            "quantity": "<quantity>",
            "unit": "<unit_of_measure>",
            "unit_price": "<unit_price>",
            "total_value": "<total_value>",
            "currency": "<currency>",
            "origin_country": "<origin_country>",
            "brand": "<brand_name>",
            "model": "<model_number>"
        }}
    ],
    "trade_terms": {{
        "incoterms": "<incoterms>",
        "payment_terms": "<payment_terms>",
        "delivery_terms": "<delivery_terms>",
        "port_of_loading": "<port_of_loading>",
        "port_of_discharge": "<port_of_discharge>"
    }},
    "financial": {{
        "total_invoice_value": "<total_value>",
        "currency": "<currency>",
        "freight_cost": "<freight_cost>",
        "insurance_cost": "<insurance_cost>",
        "other_charges": "<other_charges>"
    }},
    "additional_info": {{
        "certificates": ["<certificate_types>"],
        "special_notes": ["<special_notes>"],
        "regulatory_info": ["<regulatory_requirements>"],
        "transportation": "<transportation_details>"
    }},
    "extraction_metadata": {{
        "confidence_score": <float_0_to_1>,
        "extraction_method": "intelligent_llm_processing",
        "language_detected": "<detected_language>",
        "document_layout": "<layout_description>",
        "extraction_notes": ["<any_special_notes>"]
    }}
}}
"""
    
    @staticmethod
    def get_discrepancy_analysis_prompt(extracted_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate prompt for comprehensive discrepancy analysis.
        """
        prompt = f"""
You are an expert customs analyst with extensive experience in trade compliance and fraud detection.
Analyze the following extracted customs data for discrepancies, inconsistencies, and potential issues.

EXTRACTED DATA:
{extracted_data}
"""
        
        if reference_data:
            prompt += f"""
REFERENCE DATA (for comparison):
{reference_data}
"""
        
        prompt += """
ANALYSIS REQUIREMENTS:
Perform a comprehensive analysis covering all aspects of customs compliance and fraud detection.

1. **Value Assessment**:
   - Compare declared values with expected market prices
   - Check for currency inconsistencies
   - Identify unusually low/high valuations
   - Verify pricing relationships (unit price vs total)

2. **Product Classification**:
   - Validate product descriptions against HS codes
   - Check for tariff classification accuracy
   - Verify product origin claims
   - Identify potential dual-use items

3. **Quantity & Measurement**:
   - Check quantity and unit consistency
   - Validate weight vs volume relationships
   - Verify package count accuracy
   - Identify impossible measurements

4. **Documentation Compliance**:
   - Check for missing required information
   - Verify party details consistency
   - Validate certificate requirements
   - Check regulatory compliance

5. **Pattern Analysis**:
   - Identify suspicious trading patterns
   - Check for known fraud indicators
   - Verify business relationship authenticity
   - Analyze shipping route feasibility

6. **Risk Assessment**:
   - Evaluate overall transaction risk
   - Check against restricted/prohibited goods
   - Verify licensing requirements
   - Assess country-specific regulations

ANALYSIS OUTPUT:
Provide a detailed analysis in the following JSON format:

{{
    "analysis_summary": {{
        "total_discrepancies": <number>,
        "risk_level": "<low|medium|high|critical>",
        "overall_confidence": <float_0_to_1>,
        "requires_inspection": <boolean>,
        "automated_clearance_eligible": <boolean>
    }},
    "discrepancies": [
        {{
            "category": "<value_assessment|product_classification|quantity|documentation|pattern|risk>",
            "severity": "<low|medium|high|critical>",
            "type": "<specific_discrepancy_type>",
            "description": "<detailed_description>",
            "evidence": "<supporting_evidence>",
            "recommendation": "<specific_action_required>",
            "confidence": <float_0_to_1>
        }}
    ],
    "compliance_check": {{
        "documentation_complete": <boolean>,
        "regulatory_compliant": <boolean>,
        "licensing_required": <boolean>,
        "restricted_goods": <boolean>,
        "certificate_valid": <boolean>
    }},
    "value_analysis": {{
        "total_declared_value": "<value_and_currency>",
        "expected_value_range": "<min_max_range>",
        "value_variance": "<percentage>",
        "pricing_concerns": ["<list_of_concerns>"],
        "currency_issues": ["<currency_related_issues>"]
    }},
    "recommendations": [
        {{
            "priority": "<high|medium|low>",
            "action": "<recommended_action>",
            "rationale": "<reason_for_recommendation>",
            "timeline": "<suggested_timeline>"
        }}
    ],
    "inspection_requirements": {{
        "physical_inspection": <boolean>,
        "document_review": <boolean>,
        "laboratory_testing": <boolean>,
        "additional_documentation": <boolean>,
        "special_procedures": ["<special_procedures_needed>"]
    }},
    "analysis_metadata": {{
        "analysis_date": "<timestamp>",
        "analyst_confidence": <float_0_to_1>,
        "data_quality": "<assessment_of_input_data>",
        "analysis_method": "comprehensive_ai_analysis",
        "processing_notes": ["<any_special_notes>"]
    }}
}}
"""
        
        return prompt
    
    @staticmethod
    def get_final_report_prompt(extraction_result: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """
        Generate prompt for creating the final comprehensive report.
        """
        return f"""
You are an expert customs reporting specialist. Create a comprehensive final report 
combining the extraction results and analysis findings.

EXTRACTION RESULTS:
{extraction_result}

ANALYSIS RESULTS:
{analysis_result}

REPORT REQUIREMENTS:
Create a professional, comprehensive report suitable for customs officials and trade compliance teams.

The report should include:

1. **Executive Summary**:
   - Overall assessment
   - Key findings
   - Risk level determination
   - Recommended actions

2. **Document Overview**:
   - Document type and details
   - Parties involved
   - Transaction summary
   - Key metrics

3. **Detailed Findings**:
   - All discrepancies found
   - Evidence supporting each finding
   - Severity assessment
   - Confidence levels

4. **Compliance Assessment**:
   - Regulatory compliance status
   - Required documentation
   - Licensing requirements
   - Restricted goods check

5. **Recommendations**:
   - Immediate actions required
   - Further investigation needs
   - Processing recommendations
   - Risk mitigation strategies

Return the report in this JSON format:

{{
    "report_header": {{
        "report_id": "<unique_report_id>",
        "generation_date": "<timestamp>",
        "report_type": "customs_analysis_report",
        "version": "1.0"
    }},
    "executive_summary": {{
        "overall_assessment": "<summary_assessment>",
        "key_findings": ["<key_finding_1>", "<key_finding_2>"],
        "risk_level": "<low|medium|high|critical>",
        "clearance_recommendation": "<recommend_clearance|require_inspection|hold_for_review>",
        "confidence_score": <float_0_to_1>
    }},
    "document_overview": {{
        "document_type": "<document_type>",
        "document_number": "<document_number>",
        "transaction_value": "<total_value_currency>",
        "parties_summary": "<brief_parties_description>",
        "goods_summary": "<brief_goods_description>",
        "origin_destination": "<origin_to_destination>"
    }},
    "detailed_findings": {{
        "total_issues": <number>,
        "critical_issues": <number>,
        "high_priority_issues": <number>,
        "medium_priority_issues": <number>,
        "low_priority_issues": <number>,
        "issues_detail": [
            {{
                "issue_id": "<unique_id>",
                "category": "<category>",
                "severity": "<severity>",
                "description": "<detailed_description>",
                "evidence": "<evidence>",
                "impact": "<potential_impact>",
                "recommendation": "<specific_action>"
            }}
        ]
    }},
    "compliance_status": {{
        "overall_compliance": "<compliant|non_compliant|requires_review>",
        "documentation_status": "<complete|incomplete>",
        "regulatory_compliance": "<compliant|issues_found>",
        "licensing_status": "<not_required|valid|invalid|missing>",
        "restricted_goods_check": "<clear|flagged>",
        "compliance_notes": ["<compliance_related_notes>"]
    }},
    "recommendations": {{
        "immediate_actions": ["<action_1>", "<action_2>"],
        "investigation_required": ["<investigation_1>", "<investigation_2>"],
        "processing_recommendation": "<approve|inspect|hold|reject>",
        "follow_up_requirements": ["<follow_up_1>", "<follow_up_2>"],
        "risk_mitigation": ["<mitigation_1>", "<mitigation_2>"]
    }},
    "processing_decision": {{
        "recommended_action": "<approve|inspect|hold|reject>",
        "justification": "<reason_for_decision>",
        "required_procedures": ["<procedure_1>", "<procedure_2>"],
        "timeline": "<suggested_timeline>",
        "responsible_authority": "<authority_or_department>"
    }},
    "report_metadata": {{
        "processing_time": "<time_taken>",
        "data_sources": ["<source_1>", "<source_2>"],
        "analysis_method": "ai_assisted_comprehensive_analysis",
        "quality_score": <float_0_to_1>,
        "reviewer_required": <boolean>
    }}
}}
"""
    
    @staticmethod
    def get_error_handling_prompt(error_context: Dict[str, Any]) -> str:
        """
        Generate prompt for handling errors gracefully in the pipeline.
        """
        return f"""
You are an expert system administrator handling errors in the customs analysis pipeline.
An error occurred during processing. Please provide a structured error response.

ERROR CONTEXT:
{error_context}

REQUIREMENTS:
Provide a clear, actionable error response that helps users understand what went wrong
and what steps they can take to resolve the issue.

Return the error response in this JSON format:

{{
    "error_summary": {{
        "error_type": "<error_category>",
        "severity": "<low|medium|high|critical>",
        "user_friendly_message": "<clear_explanation>",
        "technical_details": "<technical_error_info>",
        "error_code": "<error_code>"
    }},
    "troubleshooting": {{
        "possible_causes": ["<cause_1>", "<cause_2>"],
        "recommended_solutions": ["<solution_1>", "<solution_2>"],
        "alternative_approaches": ["<approach_1>", "<approach_2>"],
        "contact_support": <boolean>
    }},
    "recovery_options": {{
        "retry_possible": <boolean>,
        "partial_results_available": <boolean>,
        "alternative_processing": <boolean>,
        "manual_intervention_required": <boolean>
    }},
    "error_metadata": {{
        "timestamp": "<error_timestamp>",
        "pipeline_stage": "<stage_where_error_occurred>",
        "input_data_quality": "<assessment>",
        "system_status": "<system_health_check>"
    }}
}}
"""


class PlaceholderData:
    """Placeholder data for testing and development."""
    
    @staticmethod
    def get_sample_pdf_content() -> str:
        """Sample PDF content for testing."""
        return """
COMMERCIAL INVOICE

Invoice No: INV-2024-0012
Date: January 15, 2024

From: ABC Electronics Ltd
      123 Industrial Park
      Shenzhen, Guangdong, China
      Tel: +86-755-1234567
      Email: export@abc-electronics.com

To: XYZ Importers Inc
    456 Business Avenue
    Los Angeles, CA 90028, USA
    Tel: +1-213-555-0123
    Email: import@xyz-importers.com

Description                    HS Code    Qty    Unit    Unit Price    Total Price
Electronic Components          8542.31    100    PCS     $150.00      $15,000.00
Semiconductor Devices          8541.10    50     PCS     $200.00      $10,000.00
Circuit Boards                 8534.00    25     PCS     $300.00      $7,500.00

                                               Subtotal:    $32,500.00
                                               Freight:     $1,500.00
                                               Insurance:   $325.00
                                               Total:       $34,325.00

Payment Terms: Net 30 Days
Incoterms: FOB Shenzhen
Origin: China
Port of Loading: Shenzhen Port
Port of Discharge: Los Angeles Port

Certificate of Origin: COO-2024-0045
Quality Certificate: QC-2024-0098
        """
    
    @staticmethod
    def get_sample_extracted_data() -> Dict[str, Any]:
        """Sample extracted data for testing."""
        return {
            "document_info": {
                "type": "commercial_invoice",
                "number": "INV-2024-0012",
                "date": "2024-01-15",
                "validity": "30 days"
            },
            "parties": {
                "seller": {
                    "name": "ABC Electronics Ltd",
                    "address": "123 Industrial Park, Shenzhen, Guangdong, China",
                    "contact": "+86-755-1234567",
                    "country": "China"
                },
                "buyer": {
                    "name": "XYZ Importers Inc",
                    "address": "456 Business Avenue, Los Angeles, CA 90028, USA",
                    "contact": "+1-213-555-0123",
                    "country": "USA"
                }
            },
            "goods": [
                {
                    "description": "Electronic Components",
                    "hs_code": "8542.31",
                    "quantity": "100",
                    "unit": "PCS",
                    "unit_price": "150.00",
                    "total_value": "15000.00",
                    "currency": "USD",
                    "origin_country": "China"
                }
            ],
            "financial": {
                "total_invoice_value": "34325.00",
                "currency": "USD",
                "freight_cost": "1500.00",
                "insurance_cost": "325.00"
            }
        }
    
    @staticmethod
    def get_sample_analysis_result() -> Dict[str, Any]:
        """Sample analysis result for testing."""
        return {
            "analysis_summary": {
                "total_discrepancies": 2,
                "risk_level": "medium",
                "overall_confidence": 0.85,
                "requires_inspection": True,
                "automated_clearance_eligible": False
            },
            "discrepancies": [
                {
                    "category": "value_assessment",
                    "severity": "medium",
                    "type": "pricing_variance",
                    "description": "Unit price for electronic components appears higher than market average",
                    "evidence": "Market price range: $120-$140, Declared: $150",
                    "recommendation": "Verify pricing with additional documentation",
                    "confidence": 0.75
                }
            ],
            "compliance_check": {
                "documentation_complete": True,
                "regulatory_compliant": True,
                "licensing_required": False,
                "restricted_goods": False,
                "certificate_valid": True
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Request additional pricing documentation",
                    "rationale": "Pricing variance requires verification",
                    "timeline": "within 5 business days"
                }
            ]
        } 