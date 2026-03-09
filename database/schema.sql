-- ─────────────────────────────────────────────
-- PYSPACE — Full Schema
-- Run in: Supabase → SQL Editor → Run
-- ─────────────────────────────────────────────

-- Drop old tables cleanly (order matters due to foreign keys)
DROP TABLE IF EXISTS interview_details CASCADE;
DROP TABLE IF EXISTS interview_questions CASCADE;
DROP TABLE IF EXISTS interview_reports CASCADE;
DROP TABLE IF EXISTS interviews CASCADE;
DROP TABLE IF EXISTS users CASCADE;


-- ─────────────────────────────────────────────
-- TABLE 1: USERS
-- ─────────────────────────────────────────────
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    email       VARCHAR(200) UNIQUE NOT NULL,
    picture     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_users (
    id            SERIAL PRIMARY KEY,
    full_name     TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);
-- ─────────────────────────────────────────────
-- TABLE 2: INTERVIEWS
-- ─────────────────────────────────────────────
CREATE TABLE interviews (
    id              SERIAL PRIMARY KEY,
    user_email      VARCHAR(200) REFERENCES users(email) ON DELETE CASCADE,
    resume_text     TEXT,                           -- Full parsed resume text (LISA reads this)
    resume_filename VARCHAR(300),                   -- Original uploaded filename
    start_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time        TIMESTAMP,                      -- Set when session completes
    status          VARCHAR(20) DEFAULT 'ongoing',  -- ongoing | completed | abandoned
    total_score     NUMERIC(5,2),                   -- Final score out of 10
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────
-- TABLE 3: INTERVIEW QUESTIONS
-- (replaces your interview_details)
-- ─────────────────────────────────────────────
CREATE TABLE interview_questions (
    id                  SERIAL PRIMARY KEY,
    interview_id        INTEGER REFERENCES interviews(id) ON DELETE CASCADE,
    question_number     INTEGER NOT NULL,           -- 1, 2, 3... (ordering)
    difficulty_level    VARCHAR(20) NOT NULL,       -- easy | medium | hard | adaptive
    topic               VARCHAR(255),              -- Python, SQL, ML etc (from resume)
    question_text       TEXT NOT NULL,
    user_answer         TEXT,
    ai_suggested_answer TEXT,
    score               NUMERIC(4,2),              -- 0.00 to 10.00
    feedback            TEXT,                      -- Per-answer tip from LISA
    asked_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────
-- TABLE 4: INTERVIEW REPORTS
-- Mirrors your uploaded report structure exactly
-- ─────────────────────────────────────────────
CREATE TABLE interview_reports (
    id                      SERIAL PRIMARY KEY,
    interview_id            INTEGER UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,

    -- Overall
    overall_score           NUMERIC(5,2),           -- e.g. 7.40
    performance_summary     TEXT,                   -- 2-3 line overall summary

    -- Skill breakdown (4 categories from your uploaded report)
    technical_knowledge     NUMERIC(4,2),           -- 0 to 10
    communication_skills    NUMERIC(4,2),
    problem_solving         NUMERIC(4,2),
    project_understanding   NUMERIC(4,2),

    -- Qualitative sections
    strengths               TEXT,                   -- What candidate did well
    areas_for_improvement   TEXT,                   -- Weak areas / gaps
    actionable_suggestions  TEXT,                   -- Study plan

    -- PDF
    report_pdf              BYTEA,                  -- Generated PDF stored here
    generated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- /*  
-- CREATE TABLE IF NOT EXISTS users (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(150),
--     email VARCHAR(200) UNIQUE,
--     picture TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- CREATE TABLE interviews (
--     id SERIAL PRIMARY KEY,
--     user_email VARCHAR(200),
--     resume_file VARCHAR(500),
--     total_score INTEGER,
--     report_pdf BYTEA,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TABLE interview_details (
--     id SERIAL PRIMARY KEY,
--     interview_id INTEGER REFERENCES interviews(id),
--     question TEXT,
--     user_answer TEXT,
--     ai_suggested_answer TEXT,
--     score INTEGER
-- );
-- -- CREATE TABLE interviews (
-- --     id SERIAL PRIMARY KEY,
-- --     user_email VARCHAR(200),
-- --     total_score INTEGER,
-- --     report_pdf BYTEA,
-- --     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- -- );

-- -- CREATE TABLE interview_details (
-- --     id SERIAL PRIMARY KEY,
-- --     interview_id INTEGER REFERENCES interviews(id),
-- --     question TEXT,
-- --     user_answer TEXT,
-- --     ai_suggested_answer TEXT,
-- --     score INTEGER
-- -- );