from sqlalchemy import (
    Column, Integer, String, Text, Numeric,
    TIMESTAMP, ForeignKey, LargeBinary
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ─────────────────────────────────────────────
# TABLE 1: USERS
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(150), nullable=False)
    email      = Column(String(200), unique=True, nullable=False)
    picture    = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    interviews = relationship("Interview", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User email={self.email}>"


# ─────────────────────────────────────────────
# TABLE 2: INTERVIEWS
# ─────────────────────────────────────────────
class Interview(Base):
    __tablename__ = "interviews"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_email      = Column(String(200), ForeignKey("users.email", ondelete="CASCADE"))
    resume_text     = Column(Text)
    resume_filename = Column(String(300))
    start_time      = Column(TIMESTAMP, server_default=func.now())
    end_time        = Column(TIMESTAMP)
    status          = Column(String(20), default="ongoing")   # ongoing | completed | abandoned
    total_score     = Column(Numeric(5, 2))
    created_at      = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user      = relationship("User", back_populates="interviews")
    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete")
    report    = relationship("InterviewReport",   back_populates="interview", cascade="all, delete", uselist=False)

    def __repr__(self):
        return f"<Interview id={self.id} user={self.user_email} status={self.status}>"


# ─────────────────────────────────────────────
# TABLE 3: INTERVIEW QUESTIONS
# ─────────────────────────────────────────────
class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    interview_id        = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"))
    question_number     = Column(Integer, nullable=False)
    difficulty_level    = Column(String(20), nullable=False)  # easy | medium | hard | adaptive
    topic               = Column(String(255))
    question_text       = Column(Text, nullable=False)
    user_answer         = Column(Text)
    ai_suggested_answer = Column(Text)
    score               = Column(Numeric(4, 2))               # 0.00 – 10.00
    feedback            = Column(Text)
    asked_at            = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    interview = relationship("Interview", back_populates="questions")

    def __repr__(self):
        return f"<InterviewQuestion #{self.question_number} level={self.difficulty_level} score={self.score}>"


# ─────────────────────────────────────────────
# TABLE 4: INTERVIEW REPORTS
# ─────────────────────────────────────────────
class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id                     = Column(Integer, primary_key=True, autoincrement=True)
    interview_id           = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), unique=True)

    # Overall
    overall_score          = Column(Numeric(5, 2))
    performance_summary    = Column(Text)

    # Skill breakdown
    technical_knowledge    = Column(Numeric(4, 2))
    communication_skills   = Column(Numeric(4, 2))
    problem_solving        = Column(Numeric(4, 2))
    project_understanding  = Column(Numeric(4, 2))

    # Qualitative
    strengths              = Column(Text)
    areas_for_improvement  = Column(Text)
    actionable_suggestions = Column(Text)

    # PDF
    report_pdf             = Column(LargeBinary)
    generated_at           = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    interview = relationship("Interview", back_populates="report")

    def __repr__(self):
        return f"<InterviewReport interview_id={self.interview_id} score={self.overall_score}>"

# from sqlalchemy import Column, Integer, String, Text, Float, DateTime
# from sqlalchemy.ext.declarative import declarative_base
# from datetime import datetime

# Base = declarative_base()

# # -------------------------
# # USERS TABLE
# # -------------------------
# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     email = Column(String, unique=True, index=True, nullable=False)
#     picture = Column(String)

# # -------------------------
# # INTERVIEW REPORT TABLE
# # -------------------------
# class InterviewReport(Base):
#     __tablename__ = "interview_reports"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, nullable=False)
#     question = Column(Text, nullable=False)
#     user_answer = Column(Text, nullable=False)
#     ai_suggested_answer = Column(Text)
#     score = Column(Float)
#     created_at = Column(DateTime, default=datetime.utcnow)