from typing import Dict, Any, Optional, List
import asyncio
from config import config
from core.llm.prompt_templates import PromptTemplates
from core.llm.system_messages import SystemPrompts
from core.llm.send_prompt_to_llm import handle_tgi_request


class LLMClient:
    """Client for handling LLM interactions."""
    
    @staticmethod
    async def analyze_customs_declaration(declaration_data: Dict[str, Any], reference_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send customs declaration to LLM for analysis.
        """
        # Prepare the messages for TGI
        messages = [
            {"role": "system", "content": SystemPrompts.general_customs_analysis()},
            {"role": "user", "content": PromptTemplates.get_customs_analysis_prompt(declaration_data, reference_data)}
        ]
        
        try:
            # Make the TGI request
            response = await handle_tgi_request(
                model_type=config.llm.TGI_MODEL_TYPE,
                messages=messages,
                temperature=config.llm.TEMPERATURE,
                max_tokens=config.llm.MAX_TOKENS
            )
            
            # Process the response
            return LLMClient.process_llm_response(str(response))
            
        except Exception as e:
            # Propagate so upstream API can return success: false
            raise
    
    @staticmethod
    def process_llm_response(response: str) -> Dict[str, Any]:
        """
        Process and validate LLM response.
        """
        try:
            # TODO: Implement actual LLM response parsing
            # This would parse the JSON response from your LLM
            import json
            
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # If not JSON, create structured response
            return {
                "discrepancies_found": 0,
                "issues": [response] if response else [],
                "recommendations": []
            }
        except Exception as e:
            return {
                "discrepancies_found": 0,
                "issues": [f"Error processing LLM response: {str(e)}"],
                "recommendations": ["Manual review required"]
            }
    
    @staticmethod
    def generate_summary_report(analysis_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary report.
        """
        discrepancies = analysis_result.get("discrepancies_found", 0)
        issues = analysis_result.get("issues", [])
        
        if discrepancies == 0:
            return f"No discrepancies found."
        else:
            summary = f"{discrepancies} discrepancies found:\n"
            for issue in issues:
                summary += f"- {issue}\n"
            return summary 