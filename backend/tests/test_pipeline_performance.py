#!/usr/bin/env python3
"""
Comprehensive pipeline performance test script.
Tests the complete pipeline from PDF parsing to LLM analysis with detailed metrics.
"""

import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
PDF_FILE_PATH = "test_data/3844_001.pdf"
RESULTS_DIR = "test_results"
PERFORMANCE_RESULTS_DIR = "performance_results"


def create_directories():
    """Create results directories if they don't exist."""
    Path(RESULTS_DIR).mkdir(exist_ok=True)
    Path(PERFORMANCE_RESULTS_DIR).mkdir(exist_ok=True)


def encode_pdf_to_base64(pdf_path: str) -> Optional[str]:
    """Encode PDF file to base64."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
            base64_content = base64.b64encode(pdf_content).decode("utf-8")
            return base64_content
    except Exception as e:
        print(f"❌ Error encoding PDF: {e}")
        return None


def get_pdf_file_info(pdf_path: str) -> Dict[str, Any]:
    """Get PDF file information."""
    try:
        path = Path(pdf_path)
        if not path.exists():
            return {"error": "File not found"}

        return {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "size_kb": round(path.stat().st_size / 1024, 2),
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "exists": True,
        }
    except Exception as e:
        return {"error": str(e)}


def test_health_check() -> Dict[str, Any]:
    """Test the health check endpoint."""
    print("🔍 Testing health check endpoint...")

    start_time = time.time()
    try:
        response = requests.get(f"{API_BASE_URL}/health-check", timeout=30)
        end_time = time.time()

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response_time_ms": round((end_time - start_time) * 1000, 2),
            "response_data": response.json() if response.status_code == 200 else response.text,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }


def test_pdf_parsing_only(pdf_content: str) -> Dict[str, Any]:
    """Test PDF parsing service only."""
    print("📄 Testing PDF parsing service...")

    # DirectParseRequest format - no options field for direct parsing
    request_data = {"file_content": pdf_content}

    start_time = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/pdf-parser/parse-direct",
            json=request_data,
            timeout=300,  # Increased timeout to 5 minutes
        )
        end_time = time.time()

        # Decide success more strictly - check both HTTP status and JSON success field
        if response.status_code == 200:
            response_data = response.json()
            parse_ok = response_data.get("success", True)
        else:
            response_data = {}
            parse_ok = False

        result = {
            "success": parse_ok,
            "status_code": response.status_code,
            "response_time_ms": round((end_time - start_time) * 1000, 2),
            "response_time_seconds": round(end_time - start_time, 2),
        }

        if parse_ok:  # Only build metrics when the parser really succeeded
            result["response_data"] = response_data

            # Extract key parser metrics for better analysis
            result["parser_metrics"] = {
                "text_content_length": len(response_data.get("text_content") or ""),
                "tables_count": len(response_data.get("tables") or []),
                "pages_count": response_data.get("metadata", {}).get("pages_count", 0),
                "ready_for_llm": response_data.get("ready_for_llm", False),
                "extraction_method": response_data.get("metadata", {}).get(
                    "extraction_method", "unknown"
                ),
            }
        else:
            if response.status_code == 200:
                result["error"] = response_data.get("error", "unknown parser error")
            else:
                result["error"] = response.text

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "response_time_seconds": round(time.time() - start_time, 2),
        }


def test_full_pipeline(pdf_content: str) -> Dict[str, Any]:
    """Test the complete pipeline."""
    print("🔄 Testing complete pipeline...")

    # FullPipelineRequest format
    request_data = {
        "file_content": pdf_content,
        "reference_data": {"test_metadata": {"test_run": True, "environment": "performance_test"}},
        "processing_options": {
            "enable_ocr": True,
            "enable_tables": True,
            "ocr_languages": ["en"],
            "confidence_threshold": 0.8,
            "deep_analysis": True,
            "generate_report": True,
        },
    }

    start_time = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/full-pipeline/process-sync",
            json=request_data,
            timeout=300,  # 5 minutes for full pipeline
        )
        end_time = time.time()

        result = {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response_time_ms": round((end_time - start_time) * 1000, 2),
            "response_time_seconds": round(end_time - start_time, 2),
        }

        if response.status_code == 200:
            response_data = response.json()
            result["response_data"] = response_data

            # Extract pipeline metrics for better analysis
            result["pipeline_metrics"] = {
                "overall_success": response_data.get("success", False),
                "pipeline_status": response_data.get("status", "unknown"),
                "task_id": response_data.get("task_id"),
                "has_complete_result": response_data.get("complete_result") is not None,
                "pipeline_stages": response_data.get("pipeline_stages"),
                "error_message": response_data.get("error"),
            }

            # Extract detailed results if available
            complete_result = response_data.get("complete_result", {})
            if complete_result:
                result["pipeline_metrics"]["complete_result_metrics"] = {
                    "overall_status": complete_result.get("overall_status"),
                    "processing_time": complete_result.get("processing_time"),
                    "pdf_extraction_success": complete_result.get("pdf_extraction", {}).get(
                        "success", False
                    ),
                    "llm_analysis_success": complete_result.get("llm_analysis", {}).get(
                        "success", False
                    ),
                    "final_report_available": complete_result.get("final_report") is not None,
                }

                # Extract PDF extraction details
                pdf_extraction = complete_result.get("pdf_extraction", {})
                if pdf_extraction:
                    result["pipeline_metrics"]["pdf_extraction_details"] = {
                        "text_content_length": len(pdf_extraction.get("text_content", "")),
                        "tables_count": len(pdf_extraction.get("tables", [])),
                        "pages_count": pdf_extraction.get("metadata", {}).get("pages_count", 0),
                        "extraction_time": pdf_extraction.get("extraction_time"),
                        "ready_for_llm": pdf_extraction.get("metadata", {}).get(
                            "ready_for_llm", False
                        ),
                    }
        else:
            result["error"] = response.text

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "response_time_seconds": round(time.time() - start_time, 2),
        }


def save_results(test_results: Dict[str, Any], filename: str):
    """Save test results to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save to performance results directory
    perf_file = Path(PERFORMANCE_RESULTS_DIR) / f"{filename}_{timestamp}.json"
    with open(perf_file, "w") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    # Also save to regular results directory
    results_file = Path(RESULTS_DIR) / f"{filename}_latest.json"
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    print(f"📁 Results saved to: {perf_file}")
    print(f"📁 Latest results: {results_file}")


def save_parser_results_details(test_results: Dict[str, Any]):
    """Save detailed parser results for analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save PDF parser results separately
    pdf_parsing = test_results.get("results", {}).get("pdf_parsing", {})
    if pdf_parsing.get("success") and pdf_parsing.get("response_data"):
        parser_file = Path(PERFORMANCE_RESULTS_DIR) / f"pdf_parser_results_{timestamp}.json"
        with open(parser_file, "w") as f:
            json.dump(pdf_parsing["response_data"], f, indent=2, ensure_ascii=False)
        print(f"📄 PDF Parser results saved to: {parser_file}")

    # Save full pipeline results separately
    full_pipeline = test_results.get("results", {}).get("full_pipeline", {})
    if full_pipeline.get("success") and full_pipeline.get("response_data"):
        pipeline_file = Path(PERFORMANCE_RESULTS_DIR) / f"full_pipeline_results_{timestamp}.json"
        with open(pipeline_file, "w") as f:
            json.dump(full_pipeline["response_data"], f, indent=2, ensure_ascii=False)
        print(f"🔄 Full Pipeline results saved to: {pipeline_file}")

        # Save complete result details if available
        complete_result = full_pipeline.get("response_data", {}).get("complete_result")
        if complete_result:
            complete_file = (
                Path(PERFORMANCE_RESULTS_DIR) / f"complete_pipeline_result_{timestamp}.json"
            )
            with open(complete_file, "w") as f:
                json.dump(complete_result, f, indent=2, ensure_ascii=False)
            print(f"📊 Complete Pipeline result saved to: {complete_file}")


def print_detailed_summary(test_results: Dict[str, Any]):
    """Print detailed summary of test results."""
    print("\n" + "=" * 60)
    print("📊 DETAILED PERFORMANCE TEST SUMMARY")
    print("=" * 60)

    health_check = test_results["results"]["health_check"]
    pdf_parsing = test_results["results"]["pdf_parsing"]
    full_pipeline = test_results["results"]["full_pipeline"]

    # Health Check
    print(
        f"🔍 Health Check: {'✅ PASS' if health_check['success'] else '❌ FAIL'} "
        f"({health_check.get('response_time_ms', 'N/A')}ms)"
    )

    # PDF Parsing Details
    print(
        f"📄 PDF Parsing: {'✅ PASS' if pdf_parsing['success'] else '❌ FAIL'} "
        f"({pdf_parsing.get('response_time_seconds', 'N/A')}s)"
    )

    if pdf_parsing.get("success") and pdf_parsing.get("parser_metrics"):
        metrics = pdf_parsing["parser_metrics"]
        print(f"   📊 Parser Metrics:")
        print(f"      • Text Content Length: {metrics.get('text_content_length', 0):,} characters")
        print(f"      • Tables Count: {metrics.get('tables_count', 0)}")
        print(f"      • Pages Count: {metrics.get('pages_count', 0)}")
        print(f"      • Ready for LLM: {metrics.get('ready_for_llm', False)}")
        print(f"      • Extraction Method: {metrics.get('extraction_method', 'unknown')}")

    # Full Pipeline Details
    print(
        f"🔄 Full Pipeline: {'✅ PASS' if full_pipeline['success'] else '❌ FAIL'} "
        f"({full_pipeline.get('response_time_seconds', 'N/A')}s)"
    )

    if full_pipeline.get("success") and full_pipeline.get("pipeline_metrics"):
        metrics = full_pipeline["pipeline_metrics"]
        print(f"   📊 Pipeline Metrics:")
        print(f"      • Overall Success: {metrics.get('overall_success', False)}")
        print(f"      • Pipeline Status: {metrics.get('pipeline_status', 'unknown')}")
        print(f"      • Task ID: {metrics.get('task_id', 'N/A')}")
        print(f"      • Has Complete Result: {metrics.get('has_complete_result', False)}")

        # Complete result details
        if metrics.get("complete_result_metrics"):
            cr_metrics = metrics["complete_result_metrics"]
            print(f"   🎯 Complete Result Metrics:")
            print(f"      • Overall Status: {cr_metrics.get('overall_status', 'unknown')}")
            print(f"      • Processing Time: {cr_metrics.get('processing_time', 'N/A')}")
            print(
                f"      • PDF Extraction Success: {cr_metrics.get('pdf_extraction_success', False)}"
            )
            print(f"      • LLM Analysis Success: {cr_metrics.get('llm_analysis_success', False)}")
            print(
                f"      • Final Report Available: {cr_metrics.get('final_report_available', False)}"
            )

        # PDF extraction details from pipeline
        if metrics.get("pdf_extraction_details"):
            pdf_details = metrics["pdf_extraction_details"]
            print(f"   📄 PDF Extraction Details (from pipeline):")
            print(
                f"      • Text Content Length: {pdf_details.get('text_content_length', 0):,} characters"
            )
            print(f"      • Tables Count: {pdf_details.get('tables_count', 0)}")
            print(f"      • Pages Count: {pdf_details.get('pages_count', 0)}")
            print(f"      • Extraction Time: {pdf_details.get('extraction_time', 'N/A')}")
            print(f"      • Ready for LLM: {pdf_details.get('ready_for_llm', False)}")

    # Overall timing
    print(f"⏱️  Total Test Time: {test_results['test_info']['total_test_time_seconds']}s")
    print(f"📄 PDF File Size: {test_results['test_info']['pdf_file']['size_kb']}KB")

    # Error details
    if not health_check["success"]:
        print(f"\n❌ Health Check Error: {health_check.get('error', 'Unknown error')}")

    if not pdf_parsing["success"]:
        print(f"\n❌ PDF Parsing Error: {pdf_parsing.get('error', 'Unknown error')}")

    if not full_pipeline["success"]:
        print(f"\n❌ Full Pipeline Error: {full_pipeline.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)


def preliminary_checks():
    """Perform preliminary checks before running the main tests."""
    print("🔍 Performing preliminary checks...")

    # Check if PDF file exists
    if not Path(PDF_FILE_PATH).exists():
        print(f"❌ PDF file not found: {PDF_FILE_PATH}")
        print("   Please ensure the test PDF file is available.")
        return False

    # Check if backend server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health-check", timeout=5)
        if response.status_code != 200:
            print(f"❌ Backend server not responding correctly: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend server at {API_BASE_URL}")
        print(f"   Error: {e}")
        print("   Please ensure the backend server is running:")
        print("   1. cd backend")
        print("   2. python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        return False

    print("✅ All preliminary checks passed!")
    return True


def main():
    """Main test function."""
    print("🚀 Starting AI Customs Pipeline Performance Test")
    print("=" * 60)

    # Perform preliminary checks
    if not preliminary_checks():
        print("\n❌ Preliminary checks failed. Please fix the issues above and try again.")
        return 1

    # Create directories
    create_directories()

    # Test start time
    overall_start = time.time()

    # Get PDF file info
    pdf_info = get_pdf_file_info(str(PDF_FILE_PATH))
    print(f"📄 PDF File: {pdf_info}")

    if pdf_info.get("error"):
        print(f"❌ Cannot access PDF file: {pdf_info['error']}")
        return 1

    # Encode PDF
    print("📝 Encoding PDF to base64...")
    pdf_content = encode_pdf_to_base64(str(PDF_FILE_PATH))
    if not pdf_content:
        print("❌ Failed to encode PDF")
        return 1

    # Initialize results
    test_results = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "pdf_file": pdf_info,
            "test_environment": {"backend_url": API_BASE_URL, "pdf_file_path": PDF_FILE_PATH},
        },
        "results": {},
    }

    # Test 1: Health Check
    test_results["results"]["health_check"] = test_health_check()

    # Test 2: PDF Parsing Only
    test_results["results"]["pdf_parsing"] = test_pdf_parsing_only(pdf_content)

    # Test 3: Full Pipeline
    test_results["results"]["full_pipeline"] = test_full_pipeline(pdf_content)

    # Overall timing
    overall_end = time.time()
    test_results["test_info"]["total_test_time_seconds"] = round(overall_end - overall_start, 2)

    # Save results
    save_results(test_results, "pipeline_performance_test")

    # Print summary
    print_detailed_summary(test_results)

    # Save individual component results for detailed analysis
    save_parser_results_details(test_results)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
