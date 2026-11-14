import os

from openai import OpenAI

PLACEHOLDER_KEY = "your-key-here"


def make_caller(client, model):
    def call_llm(messages):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    return call_llm


def make_openai_caller():
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "")

    if not api_key or api_key == PLACEHOLDER_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing. Put your key in the .env file.")
    if not model or model.startswith("put-"):
        raise RuntimeError("OPENAI_MODEL is missing. Put a model name in the .env file.")

    client = OpenAI(api_key=api_key, timeout=60, max_retries=2)
    return make_caller(client, model)