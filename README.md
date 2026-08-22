SENTINEL — Autonomous Cybersecurity Threat Intelligence

SENTINEL is a multi-agent AI system that generates structured cybersecurity intelligence reports on demand. Give it a topic — ransomware, a specific CVE class, phishing campaigns — and four specialized AI agents research it, cross-reference vulnerabilities, formulate mitigation advice, and compile a readable report, grounded in real, live web data rather than a model's static training knowledge.

Live app: https://your-app-name.streamlit.app
Live API docs: https://your-service-name.onrender.com/docs

What it does
You submit a topic through the web interface.
A Threat Intelligence Analyst agent searches the live web (via the Exa API) for recent threats related to the topic and summarizes what it finds.
A Vulnerability Researcher agent searches for newly disclosed CVEs on the same topic, cross-referencing the Analyst's findings, and lists them with severity and technical detail.
An Incident Response Advisor agent reasons over both prior outputs — no new search — and produces prioritized, concrete mitigation steps. If it flags a finding as critical, the pipeline loops back to the Analyst for a deeper follow-up pass before continuing.
A Report Writer agent compiles everything into one structured markdown report.

All of this runs asynchronously behind a REST API, backed by a persistent database, and is fully deployed and publicly accessible.

Architecture

<img width="1536" height="1024" alt="ChatGPT Image Aug 21, 2026, 08_19_58 PM" src="https://github.com/user-attachments/assets/38705014-77a2-434a-8e07-470da40c16d3" />


Project structure
.
├── main.py                    
├── database.py                 
├── app.py                     
├── langgraph_version/
│   └── graph.py                
├── crewai_reference/
│   ├── crew_test.py             
│   └── tools.py                 
├── requirements.txt
├── .env.example
└── README.md

Running it locally

1. Clone and install dependencies
bash
git clone <this-repo-url>
cd <repo-folder>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2. Set up environment variables
Copy .env.example to .env and fill in your own keys:

GROQ_API_KEY=your_groq_key
EXA_API_KEY=your_exa_key

Get a free Groq key at console.groq.com, and a free Exa key at exa.ai.

3. Run the backend
bash
uvicorn main:app --reload

Visit http://127.0.0.1:8000/docs to test the API directly.

4. Run the frontend (in a second terminal)
bash
streamlit run app.py
API endpoints
Method	Endpoint	Description
POST	/reports	Submit a topic, returns a job_id immediately (pipeline runs in the background)
GET	/reports/{job_id}	Check status (pending / done / failed) and retrieve the report once ready
GET	/reports	List all past reports
Known limitations
Report completeness depends on search retrieval quality. If a live search returns limited results, agents are explicitly instructed to omit uncertain details rather than guess — this improves accuracy but can occasionally produce a shorter report than a less careful system would.
The critical-finding severity check uses a structured signal (SEVERITY_FLAG: CRITICAL/NORMAL) rather than free-text keyword matching, specifically to avoid false positives from the model discussing severity in prose without actually flagging a real critical finding.
Free-tier hosting means the backend may take 30–60 seconds to respond after a period of inactivity (cold start).


Stack : LangGraph , CrewAI (reference) , LangChain , Groq (Llama 3) , Exa , FastAPI , SQLAlchemy , SQLite , Streamlit
