import os
from dotenv import load_dotenv
from typing import TypedDict
from exa_py import Exa
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()

exa = Exa(api_key=os.environ.get("EXA_API_KEY"))
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.3
)


class State(TypedDict):
    topic: str
    threats: str
    vulnerabilities: str
    recommendations: str
    report: str


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
    search_results = search_exa(f"recent cybersecurity threats {topic}")

    prompt = f"""You are a Threat Intelligence Analyst. Based ONLY on this real, current information:

{search_results}

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
as given above — do not mix details between different CVEs."""

    response = llm.invoke(prompt)
    state["recommendations"] = response.content
    return state


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
recombine or guess. If unsure which detail belongs to which CVE, omit it."""

    response = llm.invoke(prompt)
    state["report"] = response.content
    return state


# ── Build the graph: nodes + edges ───────────────────────────────────
def build_graph():
    graph = StateGraph(State)

    graph.add_node("analyst", threat_analyst_node)
    graph.add_node("vuln_researcher", vuln_researcher_node)
    graph.add_node("advisor", advisor_node)
    graph.add_node("writer", report_writer_node)

    graph.set_entry_point("analyst")
    graph.add_edge("analyst", "vuln_researcher")
    graph.add_edge("vuln_researcher", "advisor")
    graph.add_edge("advisor", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


def run_cyber_report(topic: str) -> str:
    app = build_graph()
    initial_state: State = {
        "topic": topic,
        "threats": "",
        "vulnerabilities": "",
        "recommendations": "",
        "report": ""
    }
    final_state = app.invoke(initial_state)
    return final_state["report"]


if __name__ == "__main__":
    topic = "ransomware"
    report = run_cyber_report(topic)
    print("\n" + "=" * 60)
    print("FINAL REPORT (LangGraph version)")
    print("=" * 60)
    print(report)