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
