import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from tools import search_cyber_news

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.3
)

# ── Agent 1: Threat Intelligence Analyst ──────────────────────────
analyst = Agent(
    role="Threat Intelligence Analyst",
    goal="Identify and summarize the most significant recent cybersecurity threats",
    backstory=(
        "You are an experienced cybersecurity analyst who monitors global threat "
        "activity daily. You base your analysis strictly on real, current sources "
        "and never invent details you weren't given."
    ),
    tools=[search_cyber_news],
    llm=llm,
    verbose=True
)

research_task = Task(
    description=(
        "Search for and analyze the most significant cybersecurity threats "
        "from the last 7 days. Focus on ransomware and major attacks."
    ),
    expected_output=(
        "A summary with 4-6 sentences covering the most significant threats found, "
        "including source context where relevant."
    ),
    agent=analyst
)

# ── Agent 2: Vulnerability Researcher ──────────────────────────────
vuln_researcher = Agent(
    role="Vulnerability Researcher",
    goal="Identify newly disclosed CVEs and assess their severity and exploitability",
    backstory=(
        "You are a vulnerability researcher who tracks newly disclosed CVEs and "
        "security advisories daily. You focus on technical accuracy: correct CVE IDs, "
        "affected software/versions, and severity, based strictly on real sources. "
        "You never invent a CVE number or severity score you weren't given."
    ),
    tools=[search_cyber_news],
    llm=llm,
    verbose=True
)

vuln_task = Task(
    description=(
        "Search for and analyze newly disclosed CVEs from the last 7 days. "
        "For each significant CVE, note the CVE ID, affected software, and severity "
        "if available. Consider the threats already identified by the Threat "
        "Intelligence Analyst as context, but focus specifically on technical "
        "vulnerability details, not general threat activity."
    ),
    expected_output=(
        "A list of 3-5 significant CVEs, each with its ID (if available), affected "
        "software, and a brief note on severity/impact."
    ),
    agent=vuln_researcher,
    context=[research_task]   # ← gives this task access to Task 1's output
)

# ── Crew: runs both tasks in sequence ──────────────────────────────
crew = Crew(
    agents=[analyst, vuln_researcher],
    tasks=[research_task, vuln_task],
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(result)