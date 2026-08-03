import os
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()

exa = Exa(api_key=os.environ.get("EXA_API_KEY"))

def search_cyber_news(query: str, num_results: int = 5):
    results = exa.search_and_contents(
        query,
        num_results=num_results,
        text=True
    )
    return results

if __name__ == "__main__":
    results = exa.search("ransomware attacks 2026", num_results=5)
    for r in results.results:
        print(r.title, r.url)