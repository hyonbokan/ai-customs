from pydantic import BaseModel, Field
from typing import List
from huggingface_hub import InferenceClient

# 1) Define your Pydantic model
class ParkObservation(BaseModel):
    location: str = Field(..., max_length=50)
    activity: str = Field(..., max_length=50)
    animals_seen: int = Field(..., ge=1, le=5)
    animals: List[str]

# 2) Export JSON Schema (a Python dict)
schema = ParkObservation.model_json_schema()

# 3) Initialize client pointing at your local TGI server
client = InferenceClient(base_url="http://localhost:8080/v1/")

# 4) Prepare messages
messages = [
    {"role": "system",  "content": "You are a helpful assistant."},
    {"role": "user",    "content": "I saw a puppy, a cat and a raccoon during my bike ride in the park."},
]

# 5) Call chat.completions with structured output
response = client.chat.completions.create(
    model="tgi",  # required: tells the server to invoke TGI
    messages=messages,
    response_format={    # must be JSON-serializable
        "type": "json",
        "value": schema  # your JSON Schema dict, not the class
    },
    max_tokens=200,
)

print(response.choices[0].message.content)
