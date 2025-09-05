"""
Declaration Analyzer Service for comprehensive customs analysis.

This service provides comprehensive LLM-based analysis capabilities and serves as
the actual business service implementation for declaration analysis in the customs pipeline.
It can be used independently for testing and modularity.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from api.routers.declaration_analyzer.helpers.data_validator import validate_declaration_data
from core.llm.llm_client import LLMClient, send_prompt_to_llm_async
from core.llm.pipeline_prompts import PipelinePrompts
from core.llm.response_models import CustomsAnalysisResponse
from core.llm.system_messages import SystemPrompts
from core.utils.logger import logger


class DeclarationAnalyzerService:
    """
    Complete Declaration Analyzer Service for comprehensive customs analysis.

    This is the actual business service implementation that can be used independently
    for testing and modularity. It performs intelligent LLM-based field extraction
    and discrepancy analysis on clean document content.

    Architecture principle: PDF parser provides clean content, LLM provides intelligent analysis.
    """

    @staticmethod
    async def initialize() -> bool:
        """Initialize the service dependencies."""
        try:
            LLMClient()  # Test LLM connectivity
            logger.info("Declaration analyzer service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize declaration analyzer service: {e}")
            return False

    async def analyze_comprehensive(
        self,
        pdf_content: str,
        tables: Optional[list] = None,
        page_content: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of customs document content.

        Args:
            pdf_content: Clean text content from PDF parser
            tables: Structured table data from PDF parser
            page_content: Page-organized content from PDF parser
            metadata: Document metadata from PDF parser
            reference_data: Optional reference data for comparison

        Returns:
            Comprehensive analysis result
        """
        analysis_id = f"analysis_{uuid4().hex[:12]}"
        start_time = datetime.now()

        pipeline_log = []
        try:
            if not await self.initialize():
                raise ValueError("Service initialization failed")

            # Validate input
            if not pdf_content:
                raise ValueError("PDF content is required for analysis")

            logger.info(f"Starting comprehensive analysis: {analysis_id}")
            pipeline_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "stage": "start",
                    "message": "Initialized service and validated input",
                    "meta": {"analysis_id": analysis_id},
                }
            )

            # Step 1: Field extraction using LLM
            field_extraction_result = await self._extract_fields_intelligently(
                pdf_content, tables, page_content, metadata
            )
            pipeline_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "stage": "field_extraction",
                    "message": "Completed field extraction",
                    "meta": {"content_processed": len(pdf_content)},
                }
            )

            # Step 2: Discrepancy analysis using LLM
            discrepancy_analysis_result = await self._analyze_discrepancies(
                field_extraction_result, reference_data
            )
            pipeline_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "stage": "discrepancy_analysis",
                    "message": "Completed discrepancy analysis",
                    "meta": {
                        "total_discrepancies": discrepancy_analysis_result.get(
                            "total_discrepancies", 0
                        )
                    },
                }
            )

            # Step 3: Generate final report
            final_report = await self._generate_comprehensive_report(
                field_extraction_result, discrepancy_analysis_result
            )
            pipeline_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "stage": "report_generation",
                    "message": "Generated final report",
                    "meta": {
                        "report_id": (
                            final_report.get("report_id")
                            if isinstance(final_report, dict)
                            else None
                        )
                    },
                }
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "analysis_id": analysis_id,
                "field_extraction": field_extraction_result,
                "discrepancy_analysis": discrepancy_analysis_result,
                "final_report": final_report,
                "pipeline_log": pipeline_log,
                "processing_summary": {
                    "fields_extracted": len(field_extraction_result.get("extracted_fields", {})),
                    "discrepancies_found": discrepancy_analysis_result.get(
                        "total_discrepancies", 0
                    ),
                    "analysis_approach": "intelligent_llm_processing",
                },
                "processing_time_seconds": processing_time,
                "metadata": {
                    "service": "declaration_analyzer_service",
                    "processing_method": "comprehensive_llm_analysis",
                },
            }

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Analysis failed for {analysis_id}: {e}")
            pipeline_log.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "stage": "error",
                    "message": "Analysis failed",
                    "meta": {"error": str(e)},
                }
            )
            return {
                "success": False,
                "analysis_id": analysis_id,
                "error": str(e),
                "pipeline_log": pipeline_log,
                "processing_time_seconds": processing_time,
                "metadata": {"service": "declaration_analyzer_service", "exception_occurred": True},
            }

    async def _extract_fields_intelligently(
        self,
        pdf_content: str,
        tables: Optional[list] = None,
        page_content: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract fields using intelligent LLM processing."""
        try:
            # Prepare comprehensive content for LLM
            combined_content = pdf_content
            if tables:
                combined_content += f"\n\nTABLE DATA:\n{tables}"
            if page_content:
                combined_content += f"\n\nPAGE STRUCTURE:\n{page_content}"

            # Get field extraction prompt
            extraction_prompt = PipelinePrompts.get_field_extraction_prompt(
                clean_content=combined_content, document_type="customs_document"
            )

            # Create messages
            messages = LLMClient.create_messages(
                user_content=extraction_prompt,
                system_content=SystemPrompts.field_extraction(),
            )

            # Send to LLM
            response = await send_prompt_to_llm_async(
                messages=messages,
                temperature=0.1,
            )

            # Process the LLM response
            extracted_data = LLMClient.process_llm_response(str(response))

            return {
                "success": True,
                "extracted_fields": extracted_data,
                "extraction_method": "intelligent_llm_processing",
                "content_processed": len(combined_content),
            }

        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            return {"success": False, "error": str(e), "extraction_method": "failed_llm_processing"}

    async def _analyze_discrepancies(
        self,
        field_extraction_result: Dict[str, Any],
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze discrepancies using intelligent LLM processing."""
        try:
            extracted_data = field_extraction_result.get("extracted_fields", {})

            # Get discrepancy analysis prompt
            analysis_prompt = PipelinePrompts.get_discrepancy_analysis_prompt(
                extracted_data=extracted_data, reference_data=reference_data
            )

            # Create messages
            messages = LLMClient.create_messages(
                user_content=analysis_prompt,
                system_content=SystemPrompts.discrepancy_analysis(),
            )

            # Send to LLM
            response = await send_prompt_to_llm_async(
                messages=messages,
                temperature=0.2,
            )

            # Process the LLM response
            analysis_data = LLMClient.process_llm_response(str(response))

            return {
                "success": True,
                "analysis_result": analysis_data,
                "total_discrepancies": analysis_data.get("analysis_summary", {}).get(
                    "total_discrepancies", 0
                ),
                "risk_level": analysis_data.get("analysis_summary", {}).get("risk_level", "medium"),
                "analysis_method": "intelligent_llm_analysis",
            }

        except Exception as e:
            logger.error(f"Discrepancy analysis failed: {e}")
            return {"success": False, "error": str(e), "analysis_method": "failed_llm_analysis"}

    async def _generate_comprehensive_report(
        self, field_extraction_result: Dict[str, Any], discrepancy_analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        try:
            # Get final report prompt
            report_prompt = PipelinePrompts.get_final_report_prompt(
                extraction_result=field_extraction_result,
                analysis_result=discrepancy_analysis_result,
            )

            # Create messages
            messages = LLMClient.create_messages(
                user_content=report_prompt,
                system_content=SystemPrompts.reporting(),
            )

            # Send to LLM
            response = await send_prompt_to_llm_async(
                messages=messages,
                temperature=0.1,
            )

            # Process the LLM response
            report_data = LLMClient.process_llm_response(str(response))

            return {
                "success": True,
                "final_report": report_data,
                "report_generation_method": "intelligent_llm_reporting",
                "report_id": f"RPT-{uuid4().hex[:12]}",
                "generation_date": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "report_generation_method": "failed_llm_reporting",
            }

    @staticmethod
    async def perform_analysis(
        declaration_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None
    ) -> CustomsAnalysisResponse:

        validation_result = validate_declaration_data(declaration_data)
        if not validation_result["is_valid"]:
            # Raise a specific error that the API route can catch and map to a 422 response
            error_details = "; ".join(validation_result["errors"])
            raise ValueError(f"Invalid declaration data: {error_details}")

        normalized_data = validation_result["normalized_data"]

        logger.info(
            f"Processing customs declaration for {normalized_data.get('declaration_number')}"
        )

        try:
            # LLMClient now returns a validated Pydantic model directly.
            analysis_report = await LLMClient.analyze_customs_declaration(
                normalized_data, reference_data
            )
            logger.info(f"LLM analysis completed for {normalized_data.get('declaration_number')}")
            return analysis_report

        except Exception as e:
            logger.error(f"Error in LLM call for {normalized_data.get('declaration_number')}: {e}")
            # The original exception is re-raised to be handled by the route,
            # which will convert it to a 502 Bad Gateway.
            raise

    @staticmethod
    async def analyze_document_sync(
        pdf_content: str,
        tables: Optional[list] = None,
        page_content: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reference_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous analysis method for direct use (not background task).

        This is the main method used by the pipeline orchestrator and for independent testing.

        Args:
            pdf_content: Clean text content from PDF parser
            tables: Structured table data from PDF parser
            page_content: Page-organized content from PDF parser
            metadata: Document metadata from PDF parser
            reference_data: Optional reference data for comparison

        Returns:
            Complete analysis result
        """
        try:
            # Create service instance for processing
            service = DeclarationAnalyzerService()

            # Use comprehensive analysis
            result = await service.analyze_comprehensive(
                pdf_content, tables, page_content, metadata, reference_data
            )

            return result

        except Exception as e:
            logger.error(f"Synchronous analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_seconds": 0.0,
                "metadata": {
                    "service": "declaration_analyzer_service",
                    "sync_processing_failed": True,
                },
            }
