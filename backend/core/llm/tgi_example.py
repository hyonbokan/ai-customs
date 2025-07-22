"""
Example usage of TGI client with structured output for customs AI analysis.

This demonstrates how to use the TGI (Text Generation Interface) client
with structured output using Pydantic models.
"""

import asyncio
import sys
import os
from typing import Dict, Any

from config import config
from core.llm.send_prompt_to_llm import handle_tgi_request
from core.llm.response_models import CustomsAnalysisResponse, PDFExtractionResponse, CityInfo
from core.llm.prompt_templates import PromptTemplates


async def example_simple_text_completion():
    """Example 1: Simple text completion without structured output."""
    print("=== Example 1: Simple Text Completion ===")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    try:
        response = await handle_tgi_request(
            model_type=config.llm.TGI_MODEL_TYPE,
            messages=messages,
            temperature=config.llm.TEMPERATURE,
            max_tokens=config.llm.MAX_TOKENS
        )
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")


async def example_structured_output():
    """Example 2: Structured output with Pydantic model."""
    print("\n=== Example 2: Structured Output ===")
    
    messages = [
        {"role": "system", "content": "You are a geography expert."},
        {"role": "user", "content": "Tell me about Paris, France. Include the population if you know it."}
    ]
    
    try:
        response = await handle_tgi_request(
            model_type=config.llm.TGI_MODEL_TYPE,
            messages=messages,
            response_model=CityInfo,
            temperature=config.llm.TEMPERATURE,
            max_tokens=config.llm.MAX_TOKENS
        )
        print(f"Structured response: {response}")
        print(f"Type: {type(response)}")
        
        if isinstance(response, CityInfo):
            print(f"City: {response.city}")
            print(f"Country: {response.country}")
            print(f"Population: {response.population}")
            if response.location:
                print(f"Location: {response.location.continent}, {response.location.region}")
            if response.key_features:
                print(f"Key Features: {', '.join(response.key_features[:3])}...")
            
    except Exception as e:
        print(f"Error: {e}")


async def example_customs_analysis():
    """Example 3: Customs declaration analysis with structured output."""
    print("\n=== Example 3: Customs Analysis ===")
    
    # Sample customs declaration data
    declaration_data = {
        "declaration_number": "CD-2024-001234",
        "importer": "ABC Trading Company",
        "goods": [
            {
                "description": "Electronic Components",
                "hs_code": "8542.31",
                "quantity": "100",
                "unit": "units",
                "value": "5000",
                "currency": "USD"
            },
            {
                "description": "Textile Products",
                "hs_code": "6204.42",
                "quantity": "50",
                "unit": "pieces",
                "value": "500",  # This is unusually low - potential issue
                "currency": "USD"
            }
        ],
        "total_value": "5500",
        "currency": "USD"
    }
    
    # Create the prompt using the template
    prompt = PromptTemplates.get_customs_analysis_prompt(declaration_data)
    
    messages = [
        {"role": "system", "content": "You are an expert customs analyst."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = await handle_tgi_request(
            model_type=config.llm.TGI_MODEL_TYPE,
            messages=messages,
            response_model=CustomsAnalysisResponse,
            temperature=config.llm.TEMPERATURE,  # Lower temperature for more consistent analysis
            max_tokens=config.llm.MAX_TOKENS
        )
        
        print(f"Analysis response: {response}")
        
        if isinstance(response, CustomsAnalysisResponse):
            print(f"Discrepancies found: {response.discrepancies_found}")
            print(f"Risk level: {response.risk_level}")
            print(f"Confidence score: {response.confidence_score}")
            print(f"Requires inspection: {response.requires_inspection}")
            
            if response.issues:
                print("\nIssues identified:")
                for issue in response.issues:
                    print(f"  - {issue.category} ({issue.severity}): {issue.description}")
                    print(f"    Recommendation: {issue.recommendation}")
            
            if response.recommendations:
                print("\nOverall recommendations:")
                for rec in response.recommendations:
                    print(f"  - {rec}")
                    
    except Exception as e:
        print(f"Error: {e}")


async def example_pdf_extraction():
    """Example 4: PDF data extraction with structured output."""
    print("\n=== Example 4: PDF Data Extraction ===")
    
    # Sample extracted PDF text
    pdf_text = """
    CUSTOMS DECLARATION
    Declaration Number: CD-2024-001235
    Declaration Date: 2024-01-15
    
    IMPORTER:
    XYZ Import Corp
    456 Trade Avenue
    Port City, USA
    Phone: +1-555-0123
    
    EXPORTER:
    Global Electronics Ltd
    789 Export Street
    Manufacturing City, China
    
    GOODS:
    1. Laptop Computers - HS Code: 8471.30 - Quantity: 50 units - Value: $75,000 USD - Origin: China
    2. Mobile Phones - HS Code: 8517.12 - Quantity: 200 units - Value: $120,000 USD - Origin: China
    
    TOTAL VALUE: $195,000 USD
    TRANSPORTATION: Sea freight via Container Ship
    """
    
    # Create the prompt using the template
    prompt = PromptTemplates.get_pdf_extraction_prompt(pdf_text)
    
    messages = [
        {"role": "system", "content": "You are an expert document processor."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = await handle_tgi_request(
            model_type=config.llm.TGI_MODEL_TYPE,
            messages=messages,
            response_model=PDFExtractionResponse,
            temperature=config.llm.TEMPERATURE,  # Very low temperature for consistent extraction
            max_tokens=config.llm.MAX_TOKENS
        )
        
        print(f"Extraction response: {response}")
        
        if isinstance(response, PDFExtractionResponse):
            print(f"Declaration Number: {response.declaration_number}")
            print(f"Declaration Date: {response.declaration_date}")
            print(f"Importer: {response.importer.name}")
            print(f"Exporter: {response.exporter.name}")
            print(f"Total Value: {response.total_value} {response.currency}")
            print(f"Extraction Confidence: {response.extraction_confidence}")
            
            print("\nGoods:")
            for good in response.goods:
                print(f"  - {good.description} (HS: {good.hs_code})")
                print(f"    Quantity: {good.quantity} {good.unit}")
                print(f"    Value: {good.value} {good.currency}")
                
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Run all examples."""
    print("TGI Client Examples with Structured Output")
    print("=" * 50)
    
    await example_simple_text_completion()
    await example_structured_output()
    await example_customs_analysis()
    await example_pdf_extraction()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 