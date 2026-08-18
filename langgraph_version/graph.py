import os
from dotenv import load_dotenv
from typing import TypedDict
from exa_py import Exa
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

exa = Exa(api_key=os.environ.get("EXA_API_KEY"))
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.3
)

MAX_CRITICAL_LOOPS = 1


class State(TypedDict):
    topic: str
    threats: str
    vulnerabilities: str
    recommendations: str
    report: str
    loop_count: int


def search_exa(query: str, num_results: int = 5) -> str:
    results = exa.search_and_contents(query, num_results=num_results, text=True)
    formatted = []
    for r in results.results:
        snippet = r.text[:800] if r.text else ""
        formatted.append(f"Title: {r.title}\nURL: {r.url}\nContent: {snippet}")
    return "\n\n---\n\n".join(formatted)


# ── Node 1: Threat Intelligence Analyst ─────────────────────────────
def threat_analyst_node(state: State) -> State:
    topic = state["topic"]
    loop_count = state.get("loop_count", 0)

    if loop_count > 0:
        query = f"detailed technical analysis of critical cybersecurity threats {topic}"
        extra_instruction = (
            "This is a FOLLOW-UP deep-dive because an earlier pass flagged something "
            "critical. Dig deeper and be more specific than a first-pass summary."
        )
    else:
        query = f"recent cybersecurity threats {topic}"
        extra_instruction = ""

    search_results = search_exa(query)

    prompt = f"""You are a Threat Intelligence Analyst. Based ONLY on this real, current information:

{search_results}

{extra_instruction}

Summarize the most significant threats related to {topic} in 4-6 sentences."""

    response = llm.invoke(prompt)
    state["threats"] = response.content
    return state


# ── Node 2: Vulnerability Researcher ────────────────────────────────
def vuln_researcher_node(state: State) -> State:
    topic = state["topic"]
    search_results = search_exa(f"newly disclosed CVEs {topic}", num_results=8)

    prompt = f"""You are a Vulnerability Researcher. Based ONLY on this real, current information:

{search_results}

Prior threat context from the Analyst:
{state['threats']}

List 3-5 significant CVEs related to {topic}. Each entry MUST follow this exact format:
'CVE-ID | Affected product | Severity | One-sentence description.'
Keep each CVE's details tightly bundled — never mix fields between different CVEs.
If you're unsure about a detail, omit it rather than guess."""

    response = llm.invoke(prompt)
    state["vulnerabilities"] = response.content
    return state


# ── Node 3: Incident Response Advisor (no search — pure reasoning) ──
def advisor_node(state: State) -> State:
    prompt = f"""You are an Incident Response Advisor. Based strictly on these findings:

THREATS:
{state['threats']}

VULNERABILITIES:
{state['vulnerabilities']}

Recommend 3-5 concrete, prioritized mitigation actions, most urgent first, with a
one-line justification each. When citing a CVE, use its exact ID and product name
as given above — do not mix details between different CVEs.

End your response with exactly one line, in exactly this format, with nothing else
on that line:
SEVERITY_FLAG: CRITICAL
or
SEVERITY_FLAG: NORMAL

Use CRITICAL only if at least one finding represents an actively-exploited,
maximum-urgency risk. Otherwise use NORMAL."""

    response = llm.invoke(prompt)
    state["recommendations"] = response.content
    state["loop_count"] = state.get("loop_count", 0) + 1
    return state


# ── Conditional check: did the Advisor flag something critical? ────
def check_criticality(state: State) -> str:
    is_critical = "SEVERITY_FLAG: CRITICAL" in state["recommendations"]
    under_loop_limit = state.get("loop_count", 0) <= MAX_CRITICAL_LOOPS

    if is_critical and under_loop_limit:
        return "loop_back"
    return "proceed"


# ── Node 4: Report Writer (no search — pure compilation) ────────────
def report_writer_node(state: State) -> State:
    prompt = f"""You are a Cybersecurity Report Writer. Compile the following into one
structured markdown report with sections: Executive Summary, Threats, Vulnerabilities,
Recommended Actions.

THREATS:
{state['threats']}

VULNERABILITIES:
{state['vulnerabilities']}

RECOMMENDATIONS:
{state['recommendations']}

Copy CVE details (ID, product, severity, description) exactly as given — never
recombine or guess. If unsure which detail belongs to which CVE, omit it.
Do not include the raw "SEVERITY_FLAG" line in your final report — it's internal only."""

    response = llm.invoke(prompt)
    state["report"] = response.content
    return state


# ── Build the graph ───────────────────────────────────────────────
def build_graph():
    graph = StateGraph(State)

    graph.add_node("analyst", threat_analyst_node)
    graph.add_node("vuln_researcher", vuln_researcher_node)
    graph.add_node("advisor", advisor_node)
    graph.add_node("writer", report_writer_node)

    graph.set_entry_point("analyst")
    graph.add_edge("analyst", "vuln_researcher")
    graph.add_edge("vuln_researcher", "advisor")

    graph.add_conditional_edges(
        "advisor",
        check_criticality,
        {
            "loop_back": "analyst",
            "proceed": "writer"
        }
    )

    graph.add_edge("writer", END)

    return graph.compile()


def run_cyber_report(topic: str) -> str:
    app = build_graph()
    initial_state: State = {
        "topic": topic,
        "threats": "",
        "vulnerabilities": "",
        "recommendations": "",
        "report": "",
        "loop_count": 0
    }
    final_state = app.invoke(initial_state)
    return final_state["report"]


if __name__ == "__main__":
    topic = "ransomware"
    report = run_cyber_report(topic)
    print("\n" + "=" * 60)
    print("FINAL REPORT (LangGraph — with conditional loop-back)")
    print("=" * 60)
    print(report)