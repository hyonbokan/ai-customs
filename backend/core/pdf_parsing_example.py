"""
Example of PDF Parsing Service Output for LLM Consumption

This example shows the clean, structured content that the PDF parsing service
provides to the LLM for intelligent field extraction and analysis.
"""

# Example output from PDF parsing service
PDF_PARSING_OUTPUT_EXAMPLE = {
    "group_id": "customs_2024_001",
    "processing_time_seconds": 12.5,
    "documents_count": 3,
    "successful_count": 3,
    "failed_count": 0,
    "documents": [
        {
            "document_id": "inv_001",
            "document_type": "commercial_invoice",
            "filename": "commercial_invoice.pdf",
            "success": True,
            "text_content": """COMMERCIAL INVOICE
                
Invoice No: INV-2024-0012
Date: January 15, 2024

From: ABC Electronics Ltd
      123 Industrial Park
      Shenzhen, China

To: XYZ Importers Inc
    456 Business Ave
    Los Angeles, CA, USA

Description          Qty    Unit Price    Total
Electronic Components 100   $150.00      $15,000.00

Total Amount: $15,000.00 USD
Payment Terms: Net 30
Origin: China""",
            "structured_data": {
                "metadata": {
                    "pages_count": 1,
                    "text_blocks_count": 12,
                    "tables_count": 1,
                    "document_type": "commercial_invoice",
                    "filename": "commercial_invoice.pdf"
                },
                "text_content": "...",  # Same as above
                "tables": [
                    {
                        "table_id": 0,
                        "page": 1,
                        "rows": 2,
                        "cols": 4,
                        "data": [
                            ["Description", "Qty", "Unit Price", "Total"],
                            ["Electronic Components", "100", "$150.00", "$15,000.00"]
                        ]
                    }
                ],
                "page_content": [
                    {
                        "page": 1,
                        "content": {
                            "texts": [
                                {"text": "COMMERCIAL INVOICE", "type": "title"},
                                {"text": "Invoice No: INV-2024-0012", "type": "text"},
                                # ... more text elements
                            ],
                            "tables": [{"table_id": 0}],
                            "pictures": []
                        }
                    }
                ],
                "document_type": "commercial_invoice"
            },
            "tables": [
                {
                    "table_id": 0,
                    "page": 1,
                    "rows": 2,
                    "cols": 4,
                    "data": [
                        ["Description", "Qty", "Unit Price", "Total"],
                        ["Electronic Components", "100", "$150.00", "$15,000.00"]
                    ]
                }
            ],
            "metadata": {
                "pages_count": 1,
                "text_blocks_count": 12,
                "tables_count": 1,
                "document_type": "commercial_invoice",
                "filename": "commercial_invoice.pdf"
            },
            "error_message": None
        },
        # ... more documents
    ],
    "completeness_analysis": {
        "completeness_score": 0.86,
        "present_document_types": [
            "commercial_invoice",
            "customs_declaration",
            "certificate_of_origin"
        ],
        "missing_critical_documents": [],
        "missing_recommended_documents": ["packing_list", "bill_of_lading"],
        "total_documents": 3,
        "successful_documents": 3,
        "failed_documents": 0,
        "ready_for_analysis": True
    },
    "ready_for_analysis": True
}

# What the LLM should extract from this content
LLM_EXPECTED_ANALYSIS = {
    "extracted_fields": {
        "commercial_invoice": {
            "invoice_number": "INV-2024-0012",
            "invoice_date": "January 15, 2024",
            "seller": "ABC Electronics Ltd, Shenzhen, China",
            "buyer": "XYZ Importers Inc, Los Angeles, CA, USA",
            "total_amount": 15000.00,
            "currency": "USD",
            "items": [
                {
                    "description": "Electronic Components",
                    "quantity": 100,
                    "unit_price": 150.00,
                    "total": 15000.00
                }
            ],
            "origin_country": "China"
        }
        # ... other documents
    },
    "discrepancies": [
        # LLM finds inconsistencies between documents
    ],
    "confidence_scores": {
        "field_extraction": 0.95,
        "discrepancy_analysis": 0.87
    }
}

"""
Key Benefits of This Approach:

1. **Language Agnostic**: PDF parser doesn't need regex for different languages
2. **Format Flexible**: LLM can handle any document layout or format  
3. **Intelligent**: LLM understands context and relationships between fields
4. **Maintainable**: No brittle regex patterns to maintain
5. **Accurate**: LLM can handle edge cases and variations
6. **Scalable**: Works with documents from any country or in any language

The PDF parser focuses on what it does best (clean extraction),
while the LLM focuses on what it does best (intelligent analysis).
""" 