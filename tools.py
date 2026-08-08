import os
from dotenv import load_dotenv
from exa_py import Exa
from crewai.tools import tool

load_dotenv()
exa = Exa(api_key=os.environ.get("EXA_API_KEY"))


@tool("Cybersecurity Search Tool")
def search_cyber_news(query: str) -> str:
    """Searches the web for recent, real cybersecurity news and threat intelligence.
    Use this to find current information about threats, attacks, or vulnerabilities."""
    results = exa.search_and_contents(query, num_results=5, text=True)

    formatted = []
    for r in results.results:
        snippet = r.text[:800] if r.text else ""
        formatted.append(f"Title: {r.title}\nURL: {r.url}\nContent: {snippet}")

    return "\n\n---\n\n".join(formatted)