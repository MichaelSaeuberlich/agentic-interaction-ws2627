"""Temporary smoke test: one plain chat completion, no tools yet."""
from openai import OpenAI

from agent.config import load_config


def main() -> None:
    cfg = load_config()
    # base_url decides which service answers (Groq, university endpoint, local model).
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key)
    response = client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "user", "content": "Explain the importance of fast language models in two sentences."}
        ],
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()