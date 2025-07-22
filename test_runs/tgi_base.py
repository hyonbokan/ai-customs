from huggingface_hub import InferenceClient

def main():
    # Note the /v1/ prefix
    client = InferenceClient(base_url="http://localhost:8080/v1/")
    
    # Chat-style call against TGI’s OpenAI-compatible chat endpoint
    response = client.chat.completions.create(
        model="tgi",  # TGI’s default model name
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is your name? and who created you?"},
        ],
        max_tokens=50,
        temperature=0.7,
        stream=False
    )
    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()