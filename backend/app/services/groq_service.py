import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_ai_response(user_message: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant for a medical clinic in Pakistan, answering patient WhatsApp queries clearly and politely."
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.5,
        max_tokens=300,
    )
    return completion.choices[0].message.content




