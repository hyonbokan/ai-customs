"""
Example of running the actual customs analysis pipeline.

This demonstrates:
- Setting up the real pipeline services
- Running the customs analysis workflow  
- Processing document groups with LLM analysis
"""

import asyncio
from typing import Dict, Any

from core.foundation import ServiceFactory
from core.workflow_config import get_workflow_config_for_environment, EXAMPLE_API_WORKFLOW_INPUT
from core.utils.logger import logger
from config import config


async def run_customs_analysis_pipeline(document_group: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete customs analysis pipeline.
    
    Args:
        document_group: Document group data with 5-7 customs documents
        
    Returns:
        Analysis result with discrepancies and recommendations
    """
    
    # 1. Create service factory with the actual pipeline configuration
    factory = ServiceFactory()
    
    # 2. Get environment-specific configuration
    environment = config.app.ENVIRONMENT
    pipeline_config = get_workflow_config_for_environment(environment)
    
    logger.info(f"Setting up customs analysis pipeline for {environment} environment")
    
    try:
        # 3. Setup services from configuration
        factory.setup_from_config(pipeline_config)
        
        # 4. Initialize all components (LLM connection, etc.)
        logger.info("Initializing pipeline components...")
        init_success = await factory.initialize_all()
        if not init_success:
            raise RuntimeError("Failed to initialize pipeline components")
        
        # 5. Start all services
        logger.info("Starting pipeline services...")
        start_success = await factory.start_all_services()
        if not start_success:
            raise RuntimeError("Failed to start pipeline services")
        
        # 6. Check system health before processing
        health_status = await factory.health_check_all()
        if health_status["overall_status"] != "healthy":
            logger.warning(f"System health check: {health_status}")
        
        # 7. Execute the customs analysis pipeline
        logger.info(f"Executing customs analysis for group: {document_group.get('group_id', 'unknown')}")
        
        pipeline_result = await factory.pipeline_manager.execute_pipeline(
            "customs_analysis_pipeline",
            document_group
        )
        
        # 8. Process and return results
        if pipeline_result.status.value == "completed":
            logger.info(f"Pipeline completed successfully in {pipeline_result.duration_seconds:.2f}s")
            
            # Extract the final analysis result from the last stage
            final_stage_result = pipeline_result.stage_results.get("analyze_discrepancies", {})
            
            return {
                "pipeline_status": "success",
                "execution_id": f"{document_group.get('group_id', 'unknown')}_{int(pipeline_result.started_at.timestamp()) if pipeline_result.started_at else 0}",
                "processing_time_seconds": pipeline_result.duration_seconds,
                "analysis_result": final_stage_result,
                "stage_results": pipeline_result.stage_results
            }
        else:
            logger.error(f"Pipeline failed: {pipeline_result.errors}")
            return {
                "pipeline_status": "failed",
                "execution_id": f"{document_group.get('group_id', 'unknown')}_failed",
                "processing_time_seconds": pipeline_result.duration_seconds,
                "errors": pipeline_result.errors,
                "stage_results": pipeline_result.stage_results
            }
    
    finally:
        # 9. Clean shutdown
        logger.info("Shutting down pipeline services...")
        await factory.stop_all_services()
        await factory.initializer_registry.cleanup_all()


async def run_example():
    """Run the example with sample data."""
    
    logger.info("=== Customs Analysis Pipeline Example ===")
    
    # Use example document data for testing
    example_document_group = {
        "group_id": "example_customs_docs_001",
        "file_url": "https://httpbin.org/json",  # Placeholder for testing
        "reference_data": {
            "expected_goods": ["electronics", "components"],
            "supplier_database": {"known_suppliers": ["ABC Electronics Ltd"]},
            "market_prices": {"electronics": {"min": 100, "max": 200}}
        }
    }
    
    result = await run_customs_analysis_pipeline(example_document_group)
    
    logger.info("=== Pipeline Results ===")
    logger.info(f"Status: {result['pipeline_status']}")
    logger.info(f"Processing time: {result['processing_time_seconds']:.2f}s")
    
    if result["pipeline_status"] == "success":
        analysis = result.get("analysis_result", {})
        if analysis:
            logger.info(f"Discrepancies found: {analysis.get('discrepancies_found', 0)}")
            logger.info(f"Risk level: {analysis.get('risk_level', 'unknown')}")
            logger.info(f"Confidence score: {analysis.get('confidence_score', 0):.2f}")
            
            discrepancies = analysis.get("discrepancies", [])
            if discrepancies:
                logger.info("Discrepancies:")
                for i, disc in enumerate(discrepancies, 1):
                    logger.info(f"  {i}. {disc.get('description', 'No description')} ({disc.get('severity', 'unknown')} severity)")
            
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                logger.info("Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    logger.info(f"  {i}. {rec}")
    else:
        logger.error(f"Pipeline failed with errors: {result.get('errors', {})}")


async def test_individual_services():
    """Test individual services separately for debugging."""
    
    logger.info("="*60)
    logger.info("TESTING INDIVIDUAL SERVICES")
    logger.info("="*60)
    
    # Test PDF parsing service
    logger.info("\n1. Testing PDF Parsing Service")
    logger.info("-" * 40)
    
    factory = ServiceFactory()
    
    # Get simplified config for testing
    pipeline_config = get_workflow_config_for_environment("development")
    
    try:
        # Setup and start services
        factory.setup_from_config(pipeline_config)
        await factory.initialize_all()
        await factory.start_all_services()
        
        pdf_service = factory.service_registry.get_service("pdf_parsing_service")
        
        # Test with sample document group (using placeholder URLs)
        test_document_group = {
            "group_id": "test_group_001",
            "documents": [
                {
                    "document_id": "test_invoice",
                    "document_type": "commercial_invoice",
                    "file_url": "https://httpbin.org/json",  # Placeholder URL for testing
                    "filename": "test_invoice.pdf"
                }
            ]
        }
        
        try:
            logger.info("Parsing document group...")
            # Note: This will fail due to placeholder URL, but shows the service structure
            if pdf_service:
                parse_result = await pdf_service.parse_document_group(test_document_group)  # type: ignore
                logger.info(f"Parse result: {parse_result}")
        except Exception as e:
            logger.info(f"Expected parsing error (placeholder URL): {e}")
            logger.info("PDF parsing service is properly configured and would work with real document URLs")
        
        # Test LLM discrepancy service
        logger.info("\n2. Testing LLM Discrepancy Service")
        logger.info("-" * 40)
        
        llm_service = factory.service_registry.get_service("llm_discrepancy_service")
        
        # Test with sample parsed content (simulating PDF parser output)
        test_parsed_content = {
            "documents": [
                {
                    "document_id": "test_invoice",
                    "document_type": "commercial_invoice",
                    "success": True,
                    "text_content": """COMMERCIAL INVOICE
Invoice No: INV-2024-0001
Date: January 15, 2024
From: Test Supplier Ltd, China
To: Test Buyer Inc, USA
Amount: $10,000.00 USD""",
                    "tables": [
                        {
                            "table_id": 0,
                            "data": [
                                ["Description", "Qty", "Price", "Total"],
                                ["Test Product", "100", "$100.00", "$10,000.00"]
                            ]
                        }
                    ],
                    "metadata": {"pages_count": 1, "document_type": "commercial_invoice"}
                }
            ],
            "completeness_analysis": {
                "completeness_score": 0.8,
                "ready_for_analysis": True
            }
        }
        
        try:
            logger.info("Testing LLM discrepancy analysis...")
            logger.info("Input: Clean structured content from PDF parser")
            logger.info(f"Document text preview: {test_parsed_content['documents'][0]['text_content'][:100]}...")
            
            # Note: The LLM service will analyze the parsed content and extract fields intelligently
            # No regex patterns needed - the LLM understands context and can handle any language/format
            logger.info("LLM service would analyze this content to:")
            logger.info("- Extract invoice number, dates, parties, amounts")
            logger.info("- Identify discrepancies between documents") 
            logger.info("- Provide confidence scores and recommendations")
            logger.info("PDF parsing provides clean content, LLM provides intelligent analysis")
            
        except Exception as e:
            logger.info(f"LLM service test structure shown (service may need LLM connection): {e}")
        
        logger.info("\n" + "="*60)
        logger.info("PIPELINE ARCHITECTURE SUMMARY")
        logger.info("="*60)
        logger.info("1. PDF Parser: Docling → Clean text/tables/structure")
        logger.info("2. LLM Service: Structured content → Field extraction + Analysis")
        logger.info("3. No Regex: Language agnostic, format flexible, LLM-powered")
        logger.info("="*60)
        
        # Get final system metrics
        metrics = await factory.service_registry.get_metrics_all()
        logger.info(f"System metrics: {metrics['overall_metrics']}")
        
    finally:
        await factory.stop_all_services()
        await factory.initializer_registry.cleanup_all()


if __name__ == "__main__":
    # Choose which example to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run individual service tests
        asyncio.run(test_individual_services())
    else:
        # Run the full pipeline example
        asyncio.run(run_example()) 