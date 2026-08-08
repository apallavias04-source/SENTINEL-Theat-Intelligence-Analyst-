import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from tools import search_cyber_news

load_dotenv()

# Connect CrewAI to Groq/Llama 3 — same key you've used since Day 1
llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0.3
)

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
    "Search for and analyze newly disclosed CVEs from the last 7 days. "
    "Focus on critical severity vulnerabilities."
    ),
    expected_output=(
        "A summary with 4-6 sentences covering the most significant threats found, "
        "including source context where relevant."
    ),
    agent=analyst
)

crew = Crew(
    agents=[analyst],
    tasks=[research_task],
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(result)