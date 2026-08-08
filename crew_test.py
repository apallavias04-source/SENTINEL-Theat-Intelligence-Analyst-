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
    context=[research_task]
)

# ── Agent 3: Incident Response Advisor ─────────────────────────────
advisor = Agent(
    role="Incident Response Advisor",
    goal="Recommend practical mitigation steps based on identified threats and vulnerabilities",
    backstory=(
        "You are a senior incident response advisor who translates raw threat and "
        "vulnerability findings into clear, actionable recommendations for a "
        "security team. You do not search for new information — you reason "
        "strictly over the findings you're given, and prioritize the most urgent "
        "actions first."
    ),
    tools=[],   # no search tool — pure reasoning over prior agents' output
    llm=llm,
    verbose=True
)

advisor_task = Task(
    description=(
        "Based on the threats identified by the Threat Intelligence Analyst and the "
        "vulnerabilities identified by the Vulnerability Researcher, recommend clear, "
        "prioritized mitigation steps. Focus on what a security team should actually "
        "do first, second, etc. Be specific where possible (e.g. 'patch X software' "
        "rather than generic advice)."
    ),
    expected_output=(
        "A prioritized list of 3-5 concrete mitigation actions, ordered from most to "
        "least urgent, with a one-line justification for each."
    ),
    agent=advisor,
    context=[research_task, vuln_task]
)

# ── Agent 4: Cybersecurity Report Writer ───────────────────────────
writer = Agent(
    role="Cybersecurity Report Writer",
    goal="Compile all findings into one clear, well-structured final report",
    backstory=(
        "You are a technical writer who specializes in cybersecurity reporting. "
        "You take findings from analysts and turn them into a clean, professional "
        "report that a non-technical manager could still follow. You do not add "
        "any new information — you only organize and clarify what you're given."
    ),
    tools=[],
    llm=llm,
    verbose=True
)

report_task = Task(
    description=(
        "Compile the threat intelligence findings, vulnerability findings, and "
        "mitigation recommendations into one structured report with these sections: "
        "'Executive Summary', 'Threats', 'Vulnerabilities', and 'Recommended Actions'. "
        "Keep it clear and readable for both technical and non-technical audiences."
    ),
    expected_output=(
        "A structured markdown report with the 4 sections listed, based strictly on "
        "the findings from the previous 3 agents."
    ),
    agent=writer,
    context=[research_task, vuln_task, advisor_task]
)

# ── Crew: all 4 agents, run in sequence ────────────────────────────
crew = Crew(
    agents=[analyst, vuln_researcher, advisor, writer],
    tasks=[research_task, vuln_task, advisor_task, report_task],
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result)