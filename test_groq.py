import os
from dotenv import load_dotenv
from groq import Groq

# Load the GROQ_API_KEY from .env into environment variables
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def ask_about_cve(cve_id: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a pirate who explains cybersecurity."
            },
            {
                "role": "user",
                "content": f"Explain what {cve_id} is, what it affects, and its severity, in 3-4 sentences."
            }
        ],
        temperature=1.0,
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    result = ask_about_cve("CVE-2023-4863")  # Log4Shell
    print(result)