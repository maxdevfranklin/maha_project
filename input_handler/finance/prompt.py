import os

from groq import Groq

client = Groq(
    api_key="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",
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)