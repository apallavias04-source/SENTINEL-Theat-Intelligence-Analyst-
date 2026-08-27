import uuid
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from langgraph_version.graph import run_cyber_report
from database import init_db, get_db, ReportJob, User
from auth import hash_password, verify_password, create_access_token, decode_access_token

app = FastAPI(title="Cybersecurity Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ── Schemas ───────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str
    password: str

class ReportRequest(BaseModel):
    topic: str

class ReportResponse(BaseModel):
    job_id: str
    status: str


# ── Auth dependency: figures out WHO is making this request ────────
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Signup ──────────────────────────────────────────────────────────
@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"user_id": new_user.id})
    return {"access_token": token, "token_type": "bearer"}


# ── Login ───────────────────────────────────────────────────────────
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}


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


# ── Submit a report — now tied to the logged-in user ─────────────────
@app.post("/reports", response_model=ReportResponse)
def create_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job_id = str(uuid.uuid4())

    new_job = ReportJob(
        job_id=job_id,
        user_id=current_user.id,
        topic=request.topic,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(new_job)
    db.commit()

    background_tasks.add_task(generate_report_task, job_id, request.topic)

    return ReportResponse(job_id=job_id, status="pending")


# ── Check a specific job — only if it belongs to you ─────────────────
@app.get("/reports/{job_id}")
def get_report(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(ReportJob).filter(
        ReportJob.job_id == job_id,
        ReportJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ── List reports — only YOUR reports, not everyone's ──────────────────
@app.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ReportJob).filter(
        ReportJob.user_id == current_user.id
    ).order_by(ReportJob.created_at.desc()).all()