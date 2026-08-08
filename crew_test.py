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


def run_cyber_report(topic: str) -> str:
    """
    Runs the full 4-agent cybersecurity intelligence pipeline for a given topic.
    Returns the final structured report as a string.
    """

    # ── Agent 1: Threat Intelligence Analyst ──────────────────────
    analyst = Agent(
        role="Threat Intelligence Analyst",
        goal=f"Identify and summarize the most significant recent cybersecurity threats related to {topic}",
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
            f"Search for and analyze the most significant cybersecurity threats "
            f"from the last 7 days related to: {topic}."
        ),
        expected_output=(
            "A summary with 4-6 sentences covering the most significant threats found, "
            "including source context where relevant."
        ),
        agent=analyst
    )

    # ── Agent 2: Vulnerability Researcher ──────────────────────────
    vuln_researcher = Agent(
        role="Vulnerability Researcher",
        goal=f"Identify newly disclosed CVEs related to {topic} and assess severity and exploitability",
        backstory=(
            "You are a vulnerability researcher who tracks newly disclosed CVEs and "
            "security advisories daily. You focus on technical accuracy: correct CVE IDs, "
            "affected software/versions, and severity, based strictly on real sources. "
            "You never invent a CVE number or severity score you weren't given. "
            "You always keep each CVE's ID, affected product, and description bundled "
            "together exactly as found — never separate them or mix details from "
            "different CVEs together."
        ),
        tools=[search_cyber_news],
        llm=llm,
        verbose=True
    )

    vuln_task = Task(
        description=(
            f"Search for and analyze newly disclosed CVEs from the last 7 days related "
            f"to: {topic}. For each significant CVE, clearly state the CVE ID, affected "
            f"software, and severity if available. Keep these three details tightly "
            f"bundled per CVE — never let details from one CVE bleed into another. "
            f"Consider the threats already identified by the Threat Intelligence "
            f"Analyst as context, but focus specifically on technical vulnerability "
            f"details, not general threat activity."
        ),
        expected_output=(
            "A numbered list of 3-5 significant CVEs. Each entry MUST follow this exact "
            "format: 'CVE-ID | Affected product | Severity | One-sentence description.' "
            "Do not deviate from this format."
        ),
        agent=vuln_researcher,
        context=[research_task]
    )

    # ── Agent 3: Incident Response Advisor ──────────────────────────
    advisor = Agent(
        role="Incident Response Advisor",
        goal="Recommend practical mitigation steps based on identified threats and vulnerabilities",
        backstory=(
            "You are a senior incident response advisor who translates raw threat and "
            "vulnerability findings into clear, actionable recommendations for a "
            "security team. You do not search for new information — you reason "
            "strictly over the findings you're given, and prioritize the most urgent "
            "actions first. When referencing a specific CVE, quote its ID and affected "
            "product exactly as given to you — never paraphrase or reconstruct it "
            "from memory."
        ),
        tools=[],
        llm=llm,
        verbose=True
    )

    advisor_task = Task(
        description=(
            "Based on the threats identified by the Threat Intelligence Analyst and the "
            "vulnerabilities identified by the Vulnerability Researcher, recommend clear, "
            "prioritized mitigation steps. Focus on what a security team should actually "
            "do first, second, etc. Be specific where possible (e.g. 'patch X software' "
            "rather than generic advice). When citing a CVE, use its exact ID and product "
            "name as given — do not mix details between different CVEs."
        ),
        expected_output=(
            "A prioritized list of 3-5 concrete mitigation actions, ordered from most to "
            "least urgent, with a one-line justification for each."
        ),
        agent=advisor,
        context=[research_task, vuln_task]
    )

    # ── Agent 4: Cybersecurity Report Writer ─────────────────────────
    writer = Agent(
        role="Cybersecurity Report Writer",
        goal="Compile all findings into one clear, well-structured final report",
        backstory=(
            "You are a technical writer who specializes in cybersecurity reporting. "
            "You take findings from analysts and turn them into a clean, professional "
            "report that a non-technical manager could still follow. You do not add "
            "any new information, and critically, you never recombine or restate CVE "
            "details from memory — you copy each CVE's ID, affected product, severity, "
            "and description exactly as they were given to you by the Vulnerability "
            "Researcher, keeping all four fields bundled together for each CVE. If you "
            "are unsure which detail belongs to which CVE, omit the detail rather than "
            "guess."
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
            "In the Vulnerabilities section, copy each CVE's ID, affected product, "
            "severity, and description exactly as provided — do not mix fields between "
            "different CVEs. Keep it clear and readable for both technical and "
            "non-technical audiences."
        ),
        expected_output=(
            "A structured markdown report with the 4 sections listed, based strictly on "
            "the findings from the previous 3 agents, with CVE details kept accurate "
            "and unmixed."
        ),
        agent=writer,
        context=[research_task, vuln_task, advisor_task]
    )

    # ── Crew: all 4 agents, run in sequence ───────────────────────────
    crew = Crew(
        agents=[analyst, vuln_researcher, advisor, writer],
        tasks=[research_task, vuln_task, advisor_task, report_task],
        verbose=True
    )

    result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    topic = "ransomware and major cyberattacks"
    report = run_cyber_report(topic)
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(report)