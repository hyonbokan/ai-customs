SO_SYSTEM_PROMPT = "You are an expert customs analyst. You will analyze documents for discrepancies and respond ONLY with a valid JSON object that strictly follows the provided schema. Ensure the `discrepancies` list is fully populated with all findings."

VEHICLE_DOCUMENT = """Analyze the provided document data for discrepancies between the Customs Declaration and the supporting documents (CVC and Bill of Lading).

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

TOYS_DOCUMENT = """Analyze the provided document data for discrepancies. A minor mismatch in naming of the goods can be ignored.

# **Customs Declaration:**
  - Item: 'Wooden Children''s Toys'
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
"""
