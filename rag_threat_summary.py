import os
from dotenv import load_dotenv
from groq import Groq
from exa_py import Exa

load_dotenv()

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
exa = Exa(api_key=os.environ.get("EXA_API_KEY"))


def retrieve_threat_data(query: str, num_results: int = 5):
    """Step 1: RETRIEVE — get real, current search results from Exa."""
    results = exa.search_and_contents(
        query,
        num_results=num_results,
        text=True
    )
    return results.results


def build_context(search_results) -> str:
    """Step 2: AUGMENT — turn raw search results into a text block for the prompt."""
    context_pieces = []
    for r in search_results:
        # Cap each article's text so the prompt doesn't get enormous
        snippet = r.text[:1000] if r.text else ""
        context_pieces.append(f"Source: {r.title}\nURL: {r.url}\nContent: {snippet}")
    return "\n\n---\n\n".join(context_pieces)


def generate_summary(context: str, topic: str) -> str:
    """Step 3: GENERATE — ask Llama 3 to reason over the real retrieved content."""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a cybersecurity threat intelligence analyst. "
                    "You will be given real, current articles. Base your summary "
                    "ONLY on the provided content — do not add information you "
                    "were not given. If the content is insufficient, say so."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\n"
                    f"Here is the retrieved content:\n\n{context}\n\n"
                    f"Write a concise threat intelligence summary (4-6 sentences) "
                    f"covering the most significant findings, and note the severity if mentioned."
                )
            }
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    topic = "latest ransomware attacks 2026"

    print(f"Retrieving real-time data for: {topic}\n")
    search_results = retrieve_threat_data(topic)

    print(f"Found {len(search_results)} sources. Building context...\n")
    context = build_context(search_results)
    print(context)

    print("Generating summary with Llama 3...\n")
    summary = generate_summary(context, topic)

    print("=" * 60)
    print("THREAT INTELLIGENCE SUMMARY")
    print("=" * 60)
    print(summary)