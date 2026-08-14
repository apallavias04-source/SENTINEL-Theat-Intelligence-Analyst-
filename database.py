from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# ── Connect to (or create) the database file ─────────────────────
DATABASE_URL = "sqlite:///./reports.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── Define the shape of a "report" row ────────────────────────────
class ReportJob(Base):
    __tablename__ = "reports"

    job_id = Column(String, primary_key=True)
    topic = Column(String, nullable=False)
    status = Column(String, default="pending")
    report = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Create the actual .db file and table, if they don't exist yet ──
def init_db():
    Base.metadata.create_all(bind=engine)


# ── Get a database session (a connection you can use to read/write) ─
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()