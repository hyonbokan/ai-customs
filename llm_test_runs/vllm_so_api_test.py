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
    {
        "role": "user",
        "content": 
"""Analyze the provided document data for discrepancies between the Customs Declaration and the supporting documents (CVC and Bill of Lading).

# **Customs Declaration (Importer's Submission)**
  - Importer: TUME TARDZENYUY JOSEPH
  - Item Description: 'Used Toyota RAV4 Passenger Vehicle'
  - Chassis Number: JTEHH20V400278836
  - Declared CIF Value: 1,210,000 XAF
  - Country of Origin: UK
  - HS Code: 8703.24.00.000 (Vehicles > 3000cc)

# **CVC - Vehicle Identification Report (Official Inspection)**
  - [cite_start]Importer: TUME TARDZENYUY JOSEPH [cite: 49]
  - [cite_start]Mark / Type: TOYOTA RAV 4 [cite: 53]
  - [cite_start]Chassis Number (N de serie): JTEHH20V400278835 [cite: 53]
  - [cite_start]Taxable Value (VALEUR IMPOSABLE): 1,460,000 XAF [cite: 73]
  - [cite_start]Engine Capacity (Cylindre): 2,000 CV [cite: 53]
  - [cite_start]HS Code (Position Tarifaire): 870323 90 990 0 [cite: 66]

# **Bill of Lading**
  - Exporter: SHENGGUAN IMP. & EXP. [cite_start]CO., LIMITED, ZHEJIANG CHINA [cite: 1745, 1749]
  - [cite_start]Port of Loading: London Gateway Port [cite: 60]
  - [cite_start]Bill of Lading No: 252573219 [cite: 54]
"""
    }
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
