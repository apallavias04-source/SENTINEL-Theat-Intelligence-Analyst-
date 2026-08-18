import uuid
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from langgraph_version.graph import run_cyber_report
from database import init_db, get_db, ReportJob

# ── Create the app FIRST, before using it anywhere ──────────────────
app = FastAPI(title="Cybersecurity Intelligence API")

# ── Allow the frontend (running on a different port) to call this API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Create the database file/table on startup, if it doesn't exist ──
init_db()


# ── Request/response shape definitions ──────────────────────────────
class ReportRequest(BaseModel):
    topic: str


class ReportResponse(BaseModel):
    job_id: str
    status: str


# ── The actual slow work, run in the background ─────────────────────
def generate_report_task(job_id: str, topic: str):
    db = next(get_db())
    try:
        report = run_cyber_report(topic)
        job = db.query(ReportJob).filter(ReportJob.job_id == job_id).first()
        job.status = "done"
        job.report = report
        db.commit()
    except Exception as e:
        job = db.query(ReportJob).filter(ReportJob.job_id == job_id).first()
        job.status = "failed"
        job.error = str(e)
        db.commit()
    finally:
        db.close()


# ── Endpoint 1: submit a new report request ──────────────────────────
@app.post("/reports", response_model=ReportResponse)
def create_report(request: ReportRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())

    new_job = ReportJob(
        job_id=job_id,
        topic=request.topic,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(new_job)
    db.commit()

    background_tasks.add_task(generate_report_task, job_id, request.topic)

    return ReportResponse(job_id=job_id, status="pending")


# ── Endpoint 2: check on a specific job ──────────────────────────────
@app.get("/reports/{job_id}")
def get_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ReportJob).filter(ReportJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ── Endpoint 3: list all jobs ─────────────────────────────────────────
@app.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    return db.query(ReportJob).order_by(ReportJob.created_at.desc()).all()