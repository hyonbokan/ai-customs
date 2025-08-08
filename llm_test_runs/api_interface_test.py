from huggingface_hub import InferenceClient

def main():
    client = InferenceClient(base_url="http://localhost:8080/v1/")

    response = client.chat.completions.create(
        model="tgi",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Introduce yourself first in French and then in English."},
        ],
        temperature=0.7,
        stream=True
    )
    for chunk in response:
        print(chunk.choices[0].delta.content, end="", flush=True)

if __name__ == "__main__":
    main()