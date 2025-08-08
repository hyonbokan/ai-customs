from pydantic import BaseModel, Field
from typing import List, Literal
from huggingface_hub import InferenceClient

# A specific piece of evidence from a document
class Evidence(BaseModel):
    document: Literal['Commercial Invoice', 'Packing List', 'Bill of Lading', 'Certificate of Origin', 'Customs Declaration'] = Field(..., description="The document where the evidence was found.")
    field: str = Field(..., description="The specific field containing the conflicting information (e.g., 'Unit Price', 'Quantity', 'HS Code').")
    value: str = Field(..., description="The conflicting value found in the field.")
    reference_location: str = Field(..., description="A specific location for the evidence, such as 'Line Item 3' or 'Total Amount section'.")

# An individual discrepancy with structured evidence
class Discrepancy(BaseModel):
    category: Literal['Valuation', 'Classification', 'Quantity', 'Origin', 'Description Mismatch'] = Field(..., description="The high-level category of the discrepancy.")
    severity: Literal['Low', 'Medium', 'High', 'Critical'] = Field(..., description="The severity level of the discrepancy.")
    description: str = Field(..., description="A concise, human-readable explanation of the discrepancy and its potential impact.")
    evidence: List[Evidence] = Field(..., description="A list of specific, conflicting pieces of evidence from the documents.")
    recommendation: str = Field(..., description="The recommended next step for the customs officer (e.g., 'Request clarification from importer', 'Flag for physical inspection').")

# The root model for the analysis summary
class AnalysisSummary(BaseModel):
    total_discrepancies: int = Field(..., ge=0, description="The total number of unique discrepancies identified.")
    risk_level: Literal['Low', 'Medium', 'High', 'Critical'] = Field(..., description="The overall risk level determined by the most severe discrepancy.")
    requires_inspection: bool = Field(..., description="A final boolean flag indicating if manual inspection is recommended.")
    summary_text: str = Field(..., description="A brief, one-paragraph summary of the findings.")

class DeclarationDiscrepancyAnalysis(BaseModel):
    analysis_summary: AnalysisSummary
    discrepancies: List[Discrepancy]

# Export JSON Schema
schema = DeclarationDiscrepancyAnalysis.model_json_schema()

# Initialize client pointing at your local TGI server
client = InferenceClient(base_url="http://localhost:8080/v1/")

# Prepare messages
messages = [
    {"role": "system", "content": "You are an expert customs analyst. You are given a customs declaration and a commercial invoice. You need to analyze the data for discrepancies."},
    {"role": "user", "content": """
Analyze the provided document data for discrepancies.

- **Customs Declaration:**
  - Item: 'Wooden Children's Toys'
  - Declared Quantity: 800 sets
  - Declared Unit Price: $10.00
  - Country of Origin: Vietnam
  - HS Code: 9503.00 (Tricycles, scooters, pedal cars and similar wheeled toys...)
- **Commercial Invoice:**
  - Description: 'Wooden Educational Blocks for Children'
  - Quantity: 800 sets
  - Unit Price: $12.00
- **Certificate of Origin:**
  - Issuer: China Council for the Promotion of International Trade
  - Country of Origin: People's Republic of China
"""}
]

# Call chat.completions with structured output
response = client.chat.completions.create(
    model="tgi",
    messages=messages,
    response_format={
        "type": "json",
        "value": schema
    },
    max_tokens=200,
    temperature=0.0,
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="", flush=True)
