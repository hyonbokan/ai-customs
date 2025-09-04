from openai import OpenAI

def main():
    client = OpenAI(
        base_url="http://localhost:8080/v1",
        api_key="",
    )

    response = client.chat.completions.create(
        model="/models/gemma-3-27b-it",
        messages=[
            {"role": "system", "content": "You are a helpful AI customs assistant."},
            {"role": "user", "content": "Introduce yourself first in French and then in English."},
            # {"role": "user", "content": "What does RAPPORT SUR LA VALEUR ET LE CLASSEMENT TARIFAIRE mean?"},
#             {
#             "role": "user",
#             "content": 
# """Analyze the provided document data for discrepancies between the Customs Declaration and the supporting documents (CVC and Bill of Lading).

# # **Customs Declaration (Importer's Submission)**
#   - Importer: TUME TARDZENYUY JOSEPH
#   - Item Description: 'Used Toyota RAV4 Passenger Vehicle'
#   - Chassis Number: JTEHH20V400278836
#   - Declared CIF Value: 1,210,000 XAF
#   - Country of Origin: UK
#   - HS Code: 8703.24.00.000 (Vehicles > 3000cc)

# # **CVC - Vehicle Identification Report (Official Inspection)**
#   - [cite_start]Importer: TUME TARDZENYUY JOSEPH [cite: 49]
#   - [cite_start]Mark / Type: TOYOTA RAV 4 [cite: 53]
#   - [cite_start]Chassis Number (N de serie): JTEHH20V400278835 [cite: 53]
#   - [cite_start]Taxable Value (VALEUR IMPOSABLE): 1,460,000 XAF [cite: 73]
#   - [cite_start]Engine Capacity (Cylindre): 2,000 CV [cite: 53]
#   - [cite_start]HS Code (Position Tarifaire): 870323 90 990 0 [cite: 66]

# # **Bill of Lading**
#   - Exporter: SHENGGUAN IMP. & EXP. [cite_start]CO., LIMITED, ZHEJIANG CHINA [cite: 1745, 1749]
#   - [cite_start]Port of Loading: London Gateway Port [cite: 60]
#   - [cite_start]Bill of Lading No: 252573219 [cite: 54]
# """
#     }
        ],
        temperature=0.7,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)

if __name__ == "__main__":
    main()
