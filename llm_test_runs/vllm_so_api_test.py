import json
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI


class Discrepancy(BaseModel):
    category: str = Field(..., description="The high-level category of the discrepancy (e.g., 'Description', 'Unit Price', 'Country of Origin').")
    risk_level: str = Field(..., description="The risk level of the discrepancy (e.g., 'High', 'Medium', 'Low').")
    description: str = Field(..., description="A concise, human-readable explanation of the discrepancy and its potential impact.")
    evidence_summary: str = Field(..., description="A single string summarizing the conflicting evidence from the documents, citing document, field, and value.")

# The root model for the analysis summary
class AnalysisSummary(BaseModel):
    total_discrepancies: int = Field(..., description="The total number of unique discrepancies identified.")
    requires_inspection: bool = Field(..., description="A final boolean flag indicating if manual inspection is recommended.")

class DeclarationDiscrepancyAnalysis(BaseModel):
    analysis_summary: AnalysisSummary
    discrepancies: List[Discrepancy] = Field(..., description="List of identified discrepancies.")

client = OpenAI(base_url="http://localhost:8080/v1/", api_key="")

# Prepare messages
messages = [
    {"role": "system", "content": "You are an expert customs analyst. You will analyze documents for discrepancies and respond ONLY with a valid JSON object that strictly follows the provided schema. Ensure the `discrepancies` list is fully populated with all findings."},
    {"role": "user", "content": """
Analyze the provided document data for discrepancies.

# **Customs Declaration:**
  - Item: 'Wooden Children's Toys'
  - Declared Quantity: 800 sets
  - Declared Unit Price: $10.00
  - Country of Origin: Vietnam
  - HS Code: 9503.00 (Tricycles, scooters, pedal cars and similar wheeled toys...)

# **Commercial Invoice:**
  - Description: 'Wooden Educational Blocks for Children'
  - Quantity: 800 sets
  - Unit Price: $12.00

# **Certificate of Origin:**
  - Issuer: China Council for the Promotion of International Trade
  - Country of Origin: People's Republic of China
"""}
]


completion = client.chat.completions.parse(
    model="/models/gemma-3-27b-it",
    messages=messages,
    response_format=DeclarationDiscrepancyAnalysis,
    max_tokens=4096,
    temperature=0.0,
)

analysis = completion.choices[0].message.parsed

print(analysis)
# Save to a file
with open("analysis_result.json", "w") as f:
    json.dump(analysis.model_dump(), f, indent=4)
