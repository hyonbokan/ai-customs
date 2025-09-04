import json
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from huggingface_hub import InferenceClient

# A simplified, flat discrepancy model
class Discrepancy(BaseModel):
    category: str = Field(..., description="The high-level category of the discrepancy (e.g., 'Valuation', 'Origin').")
    description: str = Field(..., description="A concise, human-readable explanation of the discrepancy and its potential impact.")
    evidence_summary: str = Field(..., description="A single string summarizing the conflicting evidence from the documents, citing document, field, and value.")

# The root model for the analysis summary
class AnalysisSummary(BaseModel):
    total_discrepancies: int = Field(..., description="The total number of unique discrepancies identified.")
    risk_level: str = Field(..., description="The risk level of the discrepancy (e.g., 'High', 'Medium', 'Low').")
    requires_inspection: bool = Field(..., description="A final boolean flag indicating if manual inspection is recommended.")

class DeclarationDiscrepancyAnalysis(BaseModel):
    analysis_summary: AnalysisSummary
    discrepancies: List[Discrepancy] = Field(..., description="List of identified discrepancies.")

# Export JSON Schema
schema = DeclarationDiscrepancyAnalysis.model_json_schema()

# Initialize client pointing at your local TGI server
client = InferenceClient(base_url="http://localhost:8080/v1/", timeout=60)

# Prepare messages
messages = [
    {"role": "system", "content": "You are an expert customs analyst. You will analyze documents for discrepancies and respond ONLY with a valid JSON object that strictly follows the provided schema. Ensure the `discrepancies` list is fully populated with all findings."},
    {"role": "user", "content": """
Analyze the provided document data for discrepancies. A minor mismatch in naming of the goods can be ignored.

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

response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "DeclarationDiscrepancyAnalysis",
        "schema": schema,
        "strict": True,     # guarantees schema-conformant output
    },
}


# Call chat.completions with structured output
response = client.chat.completions.create(
    model="tgi",
    messages=messages,
    response_format=response_format,
    max_tokens=4096,
    temperature=0.0,
    stream=True,
)

# Stream and collect the response
response_content = []
for chunk in response:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
        response_content.append(content)

# Save to a file
full_response = "".join(response_content)
try:
    parsed_json = json.loads(full_response)
    with open("analysis_result.json", "w") as f:
        json.dump(parsed_json, f, indent=4)
except json.JSONDecodeError:
    print("\nFailed to decode JSON. Saving raw output to raw_output.txt")
    with open("raw_output.txt", "w") as f:
        f.write(full_response)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
