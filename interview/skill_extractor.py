import os
import json
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL  = "gpt-4o-mini"


# ─────────────────────────────────────────────
# MAIN EXTRACTOR
# ─────────────────────────────────────────────
def extract_skills_projects(resume_text: str) -> dict:
    """
    Extract structured data from resume text using GPT-4o-mini.

    Args:
        resume_text: Raw text extracted from the candidate's PDF resume

    Returns:
        {
            "skills":           ["Python", "SQL", "Machine Learning", ...],
            "projects":         ["Marketing Analytics (SQL)", "Global Superstore (Power BI)", ...],
            "tools":            ["Pandas", "Tableau", "Docker", ...],
            "experience_level": "fresher" | "junior" | "mid" | "senior",
            "domains":          ["Data Analytics", "Backend", "ML", ...]
        }

    Falls back to safe defaults on any error so interview never crashes.
    """

    prompt = f"""
You are a resume parser. Extract structured information from the resume below.

Return ONLY a valid JSON object — no explanation, no markdown, no code blocks.

JSON structure:
{{
  "skills":           ["list of technical skills"],
  "projects":         ["list of project names"],
  "tools":            ["list of tools, frameworks, libraries"],
  "experience_level": "fresher | junior | mid | senior",
  "domains":          ["list of domains e.g. Data Analytics, Backend, ML, DevOps"]
}}

Rules:
- skills: programming languages, technologies, concepts
- tools: specific libraries, frameworks, platforms (e.g. Pandas, React, Docker)
- experience_level: estimate from internships/jobs (fresher=student/no exp, junior=0-2yr, mid=2-5yr, senior=5yr+)
- domains: broad areas the candidate works in
- If a field cannot be determined, return an empty list [] or "fresher" for experience_level
- Maximum 15 items per list

Resume:
{resume_text}
"""

    try:
        response = client.chat.completions.create(
            model       = MODEL,
            messages    = [{"role": "user", "content": prompt}],
            temperature = 0.2,    # Low temp for consistent structured output
            max_tokens  = 600
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if GPT adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)

        # Validate and fill missing keys with safe defaults
        return {
            "skills":           parsed.get("skills", []),
            "projects":         parsed.get("projects", []),
            "tools":            parsed.get("tools", []),
            "experience_level": parsed.get("experience_level", "fresher"),
            "domains":          parsed.get("domains", [])
        }

    except json.JSONDecodeError as e:
        print(f"[SkillExtractor] JSON parse error: {e}")
        return _fallback()

    except OpenAIError as e:
        print(f"[SkillExtractor] OpenAI error: {e}")
        return _fallback()

    except Exception as e:
        print(f"[SkillExtractor] Unexpected error: {e}")
        return _fallback()


# ─────────────────────────────────────────────
# FALLBACK
# Returns safe defaults so interview never crashes
# ─────────────────────────────────────────────
def _fallback() -> dict:
    return {
        "skills":           [],
        "projects":         [],
        "tools":            [],
        "experience_level": "fresher",
        "domains":          []
    }


# ─────────────────────────────────────────────
# HELPER — Format for LISA prompt
# Converts extracted data into a clean string
# that lisa_ai.py injects into question prompts
# ─────────────────────────────────────────────
def format_for_lisa(extracted: dict) -> str:
    """
    Convert extracted skills dict into a readable summary
    for injection into LISA's question generation prompt.

    Example output:
        Skills: Python, SQL, Machine Learning
        Projects: Marketing Analytics, Global Superstore Report
        Tools: Pandas, Power BI, Docker
        Level: junior
        Domains: Data Analytics, Backend
    """
    parts = []

    if extracted.get("skills"):
        parts.append(f"Skills: {', '.join(extracted['skills'])}")

    if extracted.get("projects"):
        parts.append(f"Projects: {', '.join(extracted['projects'])}")

    if extracted.get("tools"):
        parts.append(f"Tools: {', '.join(extracted['tools'])}")

    if extracted.get("experience_level"):
        parts.append(f"Level: {extracted['experience_level']}")

    if extracted.get("domains"):
        parts.append(f"Domains: {', '.join(extracted['domains'])}")

    return "\n".join(parts) if parts else "No structured data extracted."