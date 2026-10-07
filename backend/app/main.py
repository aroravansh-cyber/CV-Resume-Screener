# ============================================================
# ResumeAI - FastAPI Backend
# COMPLETE REPLACEMENT main.py
# ============================================================

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import threading
import re
import subprocess
import traceback


# ============================================================
# OPTIONAL LIBRARIES
# ============================================================

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    Image = None
    ImageEnhance = None
    ImageFilter = None

try:
    import pytesseract
except ImportError:
    pytesseract = None


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_MB = 10
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "jpg",
    "jpeg",
    "png",
}


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="ResumeAI API",
    description="AI-powered Resume Screening API",
    version="3.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MEMORY STORAGE
# ============================================================

screenings: Dict[str, Dict[str, Any]] = {}

lock = threading.Lock()


# ============================================================
# SKILL DATABASE
# ============================================================

SKILL_DATABASE = {
    # Programming
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "go",
    "golang",
    "rust",
    "kotlin",
    "swift",
    "dart",
    "php",
    "ruby",

    # Frontend
    "html",
    "css",
    "react",
    "react.js",
    "angular",
    "vue",
    "vue.js",
    "next.js",
    "nextjs",
    "node.js",
    "nodejs",
    "express",
    "express.js",

    # Backend
    "flask",
    "fastapi",
    "django",
    "spring",
    "spring boot",
    "rest api",
    "restful api",
    "graphql",

    # Database
    "mysql",
    "postgresql",
    "postgres",
    "sqlite",
    "mongodb",
    "firebase",
    "redis",
    "oracle",
    "sql",
    "nosql",

    # Cloud
    "aws",
    "amazon web services",
    "azure",
    "google cloud",
    "gcp",
    "docker",
    "kubernetes",

    # DevOps
    "linux",
    "bash",
    "jenkins",
    "ci/cd",
    "git",
    "github",
    "gitlab",

    # AI / ML
    "artificial intelligence",
    "ai",
    "machine learning",
    "deep learning",
    "data science",
    "data analysis",
    "numpy",
    "pandas",
    "scikit-learn",
    "sklearn",
    "tensorflow",
    "pytorch",
    "keras",
    "opencv",
    "nlp",
    "natural language processing",
    "computer vision",
    "llm",
    "generative ai",
    "generative artificial intelligence",
    "transformers",
    "hugging face",
    "yolo",

    # Visualization
    "matplotlib",
    "seaborn",
    "power bi",
    "tableau",
    "excel",

    # Mobile
    "flutter",
    "android",
    "android development",
    "ios",
    "react native",

    # Testing
    "pytest",
    "unit testing",
    "selenium",
    "postman",

    # General
    "api",
    "agile",
    "scrum",
    "communication",
    "leadership",
    "problem solving",
    "problem-solving",
    "teamwork",
}


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "python3": "python",
    "python 3": "python",

    "js": "javascript",
    "javascript es6": "javascript",

    "ts": "typescript",

    "reactjs": "react",
    "react js": "react",

    "angularjs": "angular",

    "vuejs": "vue",
    "vue js": "vue",

    "nextjs": "next.js",
    "next js": "next.js",

    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",

    "expressjs": "express",
    "express js": "express",

    "fast api": "fastapi",
    "fast-api": "fastapi",

    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgres database": "postgresql",
    "postgre sql": "postgresql",
    "postgreSQL": "postgresql",

    "mongo": "mongodb",
    "mongo db": "mongodb",

    "google cloud platform": "google cloud",

    "gcp": "google cloud",

    "aws cloud": "aws",

    "ml": "machine learning",

    "ai/ml": "machine learning",

    "artificial intelligence": "artificial intelligence",

    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",

    "tensorflow 2": "tensorflow",

    "pytorch": "pytorch",

    "cv": "computer vision",

    "nlp": "natural language processing",

    "powerbi": "power bi",

    "power-bi": "power bi",

    "problem solving": "problem solving",
    "problem-solving": "problem solving",
}


# ============================================================
# ROLE KEYWORDS
# ============================================================

ROLE_KEYWORDS = {
    "software engineer": [
        "software engineer",
        "software developer",
        "software development",
        "software engineering",
    ],

    "data scientist": [
        "data scientist",
        "data science",
        "predictive modeling",
    ],

    "machine learning engineer": [
        "machine learning engineer",
        "ml engineer",
        "machine learning",
        "deep learning",
        "model development",
    ],

    "ai engineer": [
        "ai engineer",
        "artificial intelligence engineer",
        "artificial intelligence",
        "generative ai",
        "llm",
    ],

    "frontend developer": [
        "frontend developer",
        "front end developer",
        "frontend engineer",
        "react developer",
        "ui developer",
    ],

    "backend developer": [
        "backend developer",
        "back end developer",
        "backend engineer",
        "api developer",
        "server-side developer",
    ],

    "full stack developer": [
        "full stack developer",
        "full-stack developer",
        "fullstack developer",
    ],

    "flutter developer": [
        "flutter developer",
        "flutter",
        "dart developer",
        "mobile developer",
    ],
}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ScreeningOptions(BaseModel):
    minMatchScore: float = 60
    skillSensitivity: str = "balanced"
    aiExplanation: bool = True


class CreateScreeningRequest(BaseModel):
    jobDescription: str
    options: Optional[ScreeningOptions] = None


# ============================================================
# BASIC HELPERS
# ============================================================

def generate_id() -> str:
    return uuid.uuid4().hex[:12]


def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


def allowed_file(filename: str) -> bool:
    return get_extension(filename) in ALLOWED_EXTENSIONS


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
) -> float:

    return max(
        minimum,
        min(maximum, value),
    )


def clean_text(text: str) -> str:

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = re.sub(
        r"\r\n?",
        "\n",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def normalize_for_search(text: str) -> str:

    if not text:
        return ""

    text = str(text).lower()

    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("•", " ")

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def canonical_skill(skill: str) -> str:

    skill = normalize_for_search(skill)

    if not skill:
        return ""

    if skill in SKILL_ALIASES:
        skill = SKILL_ALIASES[skill]

    return normalize_for_search(skill)


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_text(file_path: Path) -> str:

    if PdfReader is None:
        print("[WARNING] PyPDF2 is not installed.")
        return ""

    try:

        reader = PdfReader(str(file_path))

        pages = []

        for page in reader.pages:

            try:
                page_text = page.extract_text() or ""
                pages.append(page_text)

            except Exception as exc:
                print(f"[PDF PAGE ERROR] {exc}")

        return clean_text(
            "\n".join(pages)
        )

    except Exception as exc:

        print(f"[PDF ERROR] {exc}")
        return ""


# ============================================================
# DOCX EXTRACTION
# ============================================================

def extract_docx_text(file_path: Path) -> str:

    if Document is None:
        print("[WARNING] python-docx is not installed.")
        return ""

    try:

        document = Document(str(file_path))

        parts = []

        for paragraph in document.paragraphs:

            if paragraph.text:
                parts.append(paragraph.text)

        for table in document.tables:

            for row in table.rows:

                values = []

                for cell in row.cells:

                    if cell.text:
                        values.append(cell.text)

                if values:
                    parts.append(
                        " | ".join(values)
                    )

        return clean_text(
            "\n".join(parts)
        )

    except Exception as exc:

        print(f"[DOCX ERROR] {exc}")
        return ""


# ============================================================
# OLD DOC EXTRACTION
# ============================================================

def extract_doc_text(file_path: Path) -> str:

    try:

        result = subprocess.run(
            [
                "antiword",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )

        if result.returncode == 0:

            return clean_text(
                result.stdout
            )

    except Exception:
        pass

    print(
        "[WARNING] Could not extract .doc file. "
        "Install antiword or convert .doc to .docx."
    )

    return ""


# ============================================================
# IMAGE OCR
# ============================================================

def extract_image_text(file_path: Path) -> str:

    if Image is None:
        print("[WARNING] Pillow is not installed.")
        return ""

    if pytesseract is None:
        print("[WARNING] pytesseract is not installed.")
        return ""

    try:

        image = Image.open(file_path)

        if image.mode != "RGB":
            image = image.convert("RGB")

        try:

            image = image.resize(
                (
                    image.width * 2,
                    image.height * 2,
                )
            )

            if ImageEnhance:

                image = (
                    ImageEnhance.Contrast(
                        image
                    ).enhance(1.5)
                )

            if ImageFilter:

                image = image.filter(
                    ImageFilter.SHARPEN
                )

        except Exception:
            pass

        text = pytesseract.image_to_string(
            image,
            config="--psm 6",
        )

        return clean_text(text)

    except Exception as exc:

        print(f"[OCR ERROR] {exc}")
        return ""


# ============================================================
# GENERAL RESUME EXTRACTION
# ============================================================

def extract_resume_text(
    file_path: Path,
) -> str:

    extension = get_extension(
        file_path.name
    )

    if extension == "pdf":
        return extract_pdf_text(file_path)

    if extension == "docx":
        return extract_docx_text(file_path)

    if extension == "doc":
        return extract_doc_text(file_path)

    if extension in {
        "jpg",
        "jpeg",
        "png",
    }:
        return extract_image_text(file_path)

    return ""


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text: str) -> List[str]:

    normalized = normalize_for_search(text)

    if not normalized:
        return []

    found: Dict[str, str] = {}

    # Check canonical database skills
    for skill in SKILL_DATABASE:

        canonical = canonical_skill(skill)

        if not canonical:
            continue

        # Convert special characters to safe regex
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(canonical)
            + r"(?![a-z0-9])"
        )

        try:

            if re.search(
                pattern,
                normalized,
                re.IGNORECASE,
            ):

                found[canonical] = skill

        except re.error:

            if canonical in normalized:
                found[canonical] = skill

    # Check aliases explicitly
    for alias, canonical in SKILL_ALIASES.items():

        alias_normalized = normalize_for_search(
            alias
        )

        canonical_normalized = canonical_skill(
            canonical
        )

        if not alias_normalized:
            continue

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(alias_normalized)
            + r"(?![a-z0-9])"
        )

        try:

            if re.search(
                pattern,
                normalized,
                re.IGNORECASE,
            ):

                # Find canonical display name
                display = canonical_normalized

                for database_skill in SKILL_DATABASE:

                    if canonical_skill(
                        database_skill
                    ) == canonical_normalized:

                        display = database_skill
                        break

                found[
                    canonical_normalized
                ] = display

        except re.error:
            pass

    return sorted(
        set(found.values()),
        key=lambda value: value.lower(),
    )


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(
    text: str,
    filename: str = "",
) -> str:

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    explicit_patterns = [
        r"^(?:name|candidate name|full name)"
        r"\s*[:\-]\s*(.+)$",

        r"^(?:candidate)"
        r"\s*[:\-]\s*(.+)$",
    ]

    for line in lines[:30]:

        for pattern in explicit_patterns:

            match = re.match(
                pattern,
                line,
                re.IGNORECASE,
            )

            if match:

                name = match.group(1).strip()

                name = re.sub(
                    r"\s{2,}",
                    " ",
                    name,
                )

                if 2 <= len(name.split()) <= 6:
                    return name

    blocked_words = {
        "resume",
        "curriculum",
        "vitae",
        "cv",
        "profile",
        "summary",
        "objective",
        "experience",
        "education",
        "skills",
        "skill",
        "contact",
        "email",
        "phone",
        "mobile",
        "address",
        "location",
        "developer",
        "engineer",
        "student",
        "projects",
        "project",
        "internship",
        "intern",
        "linkedin",
        "github",
        "portfolio",
    }

    for line in lines[:20]:

        clean = re.sub(
            r"[^A-Za-z .'-]",
            "",
            line,
        ).strip()

        clean = re.sub(
            r"\s{2,}",
            " ",
            clean,
        )

        words = clean.split()

        if len(words) < 2:
            continue

        if len(words) > 5:
            continue

        lower = clean.lower()

        if any(
            word in lower
            for word in blocked_words
        ):
            continue

        if "@" in clean:
            continue

        valid_name = all(
            re.match(
                r"^[A-Za-z][A-Za-z.'-]*$",
                word,
            )
            for word in words
        )

        if valid_name:
            return clean.title()

    # Filename fallback
    if filename:

        stem = Path(filename).stem

        stem = re.sub(
            r"^[a-f0-9]{6,16}_",
            "",
            stem,
            flags=re.IGNORECASE,
        )

        stem = re.sub(
            r"whatsapp image\s*",
            "",
            stem,
            flags=re.IGNORECASE,
        )

        stem = re.sub(
            r"\b(resume|cv|final|updated|new)\b",
            "",
            stem,
            flags=re.IGNORECASE,
        )

        stem = re.sub(
            r"[_\-]+",
            " ",
            stem,
        )

        stem = re.sub(
            r"\s+",
            " ",
            stem,
        ).strip()

        if stem and not re.fullmatch(
            r"[\d .:_-]+",
            stem,
        ):
            return stem.title()

    return "Unknown Candidate"


# ============================================================
# LOCATION
# ============================================================

def extract_location(text: str) -> str:

    patterns = [
        r"(?:location|address|city)"
        r"\s*[:\-]\s*([^\n]+)",

        r"(?:based in|located in)"
        r"\s+([A-Za-z ,.-]{3,80})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            value = match.group(1).strip()

            value = re.sub(
                r"\s{2,}",
                " ",
                value,
            )

            return value[:100]

    cities = [
        "Dehradun",
        "Delhi",
        "New Delhi",
        "Noida",
        "Gurugram",
        "Gurgaon",
        "Haridwar",
        "Rishikesh",
        "Chandigarh",
        "Mumbai",
        "Pune",
        "Bangalore",
        "Bengaluru",
        "Hyderabad",
        "Chennai",
        "Kolkata",
        "Jaipur",
        "Lucknow",
        "Ahmedabad",
        "Indore",
        "Kanpur",
        "Agra",
        "Hathras",
    ]

    lower = text.lower()

    for city in cities:

        if city.lower() in lower:
            return city

    return "Not specified"


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_year_number(
    text: str,
) -> Optional[float]:

    if not text:
        return None

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*"
        r"(?:years?|yrs?)"
        r"(?:\s+of)?\s+experience",

        r"experience\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\+?\s*"
        r"(?:years?|yrs?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            normalize_for_search(text),
            re.IGNORECASE,
        )

        if match:
            return safe_float(
                match.group(1),
                0,
            )

    return None


def extract_experience(
    text: str,
) -> str:

    years = extract_year_number(text)

    if years is not None:

        if years == int(years):
            return f"{int(years)} years"

        return f"{years:g} years"

    if re.search(
        r"\bintern(ship)?\b",
        text,
        re.IGNORECASE,
    ):
        return "Internship experience"

    if re.search(
        r"\bfresher\b|"
        r"\bfresh graduate\b|"
        r"\brecent graduate\b",
        text,
        re.IGNORECASE,
    ):
        return "Fresher"

    return "Not specified"


# ============================================================
# ROLE
# ============================================================

def extract_role(text: str) -> str:

    normalized = normalize_for_search(text)

    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            keyword_normalized = normalize_for_search(
                keyword
            )

            if keyword_normalized in normalized:
                return role.title()

    return "Candidate"


# ============================================================
# EMAIL
# ============================================================

def extract_email(text: str) -> str:

    match = re.search(
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}\b",
        text,
    )

    if match:
        return match.group(0)

    return ""


# ============================================================
# PHONE
# ============================================================

def extract_phone(text: str) -> str:

    patterns = [
        r"(?<!\d)"
        r"(?:\+91[\s-]?)?"
        r"[6-9]\d{9}"
        r"(?!\d)",

        r"(?<!\d)"
        r"\+91[\s-]?[6-9]\d{9}"
        r"(?!\d)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
        )

        if match:
            return match.group(0)

    return ""


# ============================================================
# JOB DESCRIPTION ANALYSIS
# ============================================================

def analyze_job_description(
    job_description: str,
) -> Dict[str, Any]:

    skills = extract_skills(
        job_description
    )

    role = extract_role(
        job_description
    )

    required_years = extract_year_number(
        job_description
    )

    return {
        "skills": skills,
        "role": role,
        "skillCount": len(skills),
        "requiredYears": required_years,
    }


# ============================================================
# CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    resume_text: str,
    filename: str,
) -> Dict[str, Any]:

    skills = extract_skills(
        resume_text
    )

    return {
        "name": extract_name(
            resume_text,
            filename,
        ),

        "role": extract_role(
            resume_text,
        ),

        "experience": extract_experience(
            resume_text,
        ),

        "location": extract_location(
            resume_text,
        ),

        "email": extract_email(
            resume_text,
        ),

        "phone": extract_phone(
            resume_text,
        ),

        "skills": skills,
    }


# ============================================================
# SKILL MATCHING
# ============================================================

def calculate_skill_match(
    jd_skills: List[str],
    candidate_skills: List[str],
    sensitivity: str = "balanced",
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Create canonical JD skill map
    # --------------------------------------------------------

    jd_map: Dict[str, str] = {}

    for skill in jd_skills:

        canonical = canonical_skill(skill)

        if canonical:
            jd_map[canonical] = skill

    # --------------------------------------------------------
    # Candidate canonical skills
    # --------------------------------------------------------

    candidate_set = set()

    for skill in candidate_skills:

        canonical = canonical_skill(skill)

        if canonical:
            candidate_set.add(canonical)

    # --------------------------------------------------------
    # No skills in JD
    # --------------------------------------------------------

    if not jd_map:

        return {
            "score": 100.0,
            "matched": [],
            "missing": [],
        }

    # --------------------------------------------------------
    # Match
    # --------------------------------------------------------

    matched_normalized = set()

    for jd_skill in jd_map:

        # Exact canonical match
        if jd_skill in candidate_set:

            matched_normalized.add(
                jd_skill
            )
            continue

        # Partial/related match
        for candidate_skill in candidate_set:

            if (
                jd_skill in candidate_skill
                or candidate_skill in jd_skill
            ):

                matched_normalized.add(
                    jd_skill
                )
                break

    # --------------------------------------------------------
    # Missing
    # --------------------------------------------------------

    missing_normalized = (
        set(jd_map.keys())
        - matched_normalized
    )

    matched = [
        jd_map[item]
        for item in matched_normalized
        if item in jd_map
    ]

    missing = [
        jd_map[item]
        for item in missing_normalized
        if item in jd_map
    ]

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score = (
        len(matched_normalized)
        / len(jd_map)
    ) * 100

    sensitivity = str(
        sensitivity or "balanced"
    ).lower()

    if sensitivity == "strict":

        score *= 0.95

    elif sensitivity == "flexible":

        score = min(
            100,
            score * 1.05 + 3,
        )

    score = clamp(
        round(score, 1)
    )

    return {
        "score": score,
        "matched": sorted(matched),
        "missing": sorted(missing),
    }


# ============================================================
# EXPERIENCE SCORE
# ============================================================

def calculate_experience_score(
    job_description: str,
    resume_text: str,
) -> float:

    required_years = extract_year_number(
        job_description
    )

    candidate_years = extract_year_number(
        resume_text
    )

    # --------------------------------------------------------
    # IMPORTANT FIX
    #
    # If JD does NOT specify experience,
    # experience should NOT affect the final score.
    # --------------------------------------------------------

    if required_years is None:

        return 100.0

    if required_years <= 0:

        return 100.0

    if candidate_years is None:

        return 0.0

    if candidate_years >= required_years:

        return 100.0

    ratio = (
        candidate_years
        / required_years
    )

    return clamp(
        round(
            ratio * 100,
            1,
        )
    )


# ============================================================
# FINAL SCORE
# ============================================================

def calculate_final_score(
    skill_score: float,
    experience_score: float,
    job_description: str,
) -> float:

    required_years = extract_year_number(
        job_description
    )

    # --------------------------------------------------------
    # IMPORTANT FIX:
    #
    # If experience is NOT mentioned in JD,
    # use skill score directly.
    #
    # This prevents:
    #
    # skill = 0
    # experience = 100
    #
    # from becoming 15%.
    # --------------------------------------------------------

    if required_years is None:

        final_score = skill_score

    else:

        # Skills = 85%
        # Experience = 15%

        final_score = (
            skill_score * 0.85
            + experience_score * 0.15
        )

    return clamp(
        round(
            final_score,
            1,
        )
    )


# ============================================================
# EXPLANATION
# ============================================================

def generate_explanation(
    candidate: Dict[str, Any],
    job_analysis: Dict[str, Any],
    match_result: Dict[str, Any],
    final_score: float,
) -> str:

    matched = match_result["matched"]
    missing = match_result["missing"]

    jd_skills = job_analysis["skills"]

    if final_score >= 80:

        level = "Strong match"

    elif final_score >= 60:

        level = "Moderate match"

    elif final_score >= 40:

        level = "Partial match"

    else:

        level = "Low match"

    parts = []

    parts.append(
        f"{level}. "
        f"The candidate matches "
        f"{len(matched)} of "
        f"{len(jd_skills)} "
        f"identified job skills."
    )

    if matched:

        preview = ", ".join(
            matched[:8]
        )

        parts.append(
            f"Matching skills include "
            f"{preview}."
        )

    if missing:

        preview = ", ".join(
            missing[:8]
        )

        parts.append(
            f"Skills that may need "
            f"improvement include "
            f"{preview}."
        )

    parts.append(
        "Experience information: "
        f"{candidate.get('experience', 'Not specified')}."
    )

    return " ".join(parts)


# ============================================================
# PROCESS ONE RESUME
# ============================================================

def process_candidate(
    file_path: Path,
    job_analysis: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:

    filename = file_path.name

    print("=" * 60)
    print(f"[PROCESSING] {filename}")

    # --------------------------------------------------------
    # Extract resume text
    # --------------------------------------------------------

    resume_text = extract_resume_text(
        file_path
    )

    print(
        f"[TEXT LENGTH] {len(resume_text)} characters"
    )

    if not resume_text:

        print(
            f"[WARNING] No text extracted from {filename}"
        )

    # --------------------------------------------------------
    # Analyze candidate
    # --------------------------------------------------------

    candidate = analyze_candidate(
        resume_text,
        filename,
    )

    print(
        "[CANDIDATE NAME]",
        candidate["name"],
    )

    print(
        "[CANDIDATE SKILLS]",
        candidate["skills"],
    )

    # --------------------------------------------------------
    # Skill matching
    # --------------------------------------------------------

    match_result = calculate_skill_match(
        job_analysis["skills"],
        candidate["skills"],
        options.get(
            "skillSensitivity",
            "balanced",
        ),
    )

    skill_score = match_result["score"]

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    experience_score = calculate_experience_score(
        options.get(
            "jobDescription",
            "",
        ),
        resume_text,
    )

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    final_score = calculate_final_score(
        skill_score,
        experience_score,
        options.get(
            "jobDescription",
            "",
        ),
    )

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    explanation = generate_explanation(
        candidate,
        job_analysis,
        match_result,
        final_score,
    )

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    print(
        "[JD SKILLS]",
        job_analysis["skills"],
    )

    print(
        "[MATCHED SKILLS]",
        match_result["matched"],
    )

    print(
        "[MISSING SKILLS]",
        match_result["missing"],
    )

    print(
        "[SKILL SCORE]",
        skill_score,
    )

    print(
        "[EXPERIENCE SCORE]",
        experience_score,
    )

    print(
        "[FINAL SCORE]",
        final_score,
    )

    print("=" * 60)

    return {

        "name": candidate["name"],

        "role": candidate["role"],

        "experience": candidate["experience"],

        "location": candidate["location"],

        "email": candidate["email"],

        "phone": candidate["phone"],

        "skills": candidate["skills"],

        "matchedSkills": (
            match_result["matched"]
        ),

        "missingSkills": (
            match_result["missing"]
        ),

        "skillScore": skill_score,

        "experienceScore": experience_score,

        "matchScore": final_score,

        "score": final_score,

        "explanation": explanation,

        "resumeFilename": filename,

        "resumeUrl": None,

        # Internal
        "resumeText": resume_text,
    }


# ============================================================
# UPDATE SCREENING
# ============================================================

def update_screening(
    screening_id: str,
    **values,
):

    with lock:

        screening = screenings.get(
            screening_id
        )

        if not screening:
            return

        screening.update(values)


# ============================================================
# BACKGROUND SCREENING
# ============================================================

def run_screening(
    screening_id: str,
):

    try:

        with lock:

            screening = screenings.get(
                screening_id
            )

            if not screening:
                return

            job_description = screening[
                "jobDescription"
            ]

            options = dict(
                screening["options"]
            )

            files = list(
                screening["files"]
            )

        # ----------------------------------------------------
        # STEP 1
        # ----------------------------------------------------

        update_screening(
            screening_id,

            currentStep="readingJobDescription",

            progress=10,

            statusMessage=(
                "Reading job description..."
            ),
        )

        job_analysis = analyze_job_description(
            job_description
        )

        options["jobDescription"] = (
            job_description
        )

        print("=" * 60)
        print("[JOB DESCRIPTION ANALYSIS]")
        print(
            "[JOB ROLE]",
            job_analysis["role"],
        )
        print(
            "[JOB SKILLS]",
            job_analysis["skills"],
        )
        print(
            "[REQUIRED YEARS]",
            job_analysis["requiredYears"],
        )
        print("=" * 60)

        # ----------------------------------------------------
        # STEP 2
        # ----------------------------------------------------

        update_screening(
            screening_id,

            currentStep="uploadingCvs",

            progress=25,

            statusMessage=(
                "Preparing resumes..."
            ),
        )

        # ----------------------------------------------------
        # STEP 3
        # ----------------------------------------------------

        candidates = []

        total_files = len(files)

        for index, file_info in enumerate(files):

            filename = file_info[
                "filename"
            ]

            path = Path(
                file_info["path"]
            )

            progress = (
                30
                + (
                    (index + 1)
                    / max(total_files, 1)
                )
                * 25
            )

            update_screening(
                screening_id,

                currentStep=(
                    "extractingInformation"
                ),

                progress=progress,

                statusMessage=(
                    f"Reading {filename}..."
                ),
            )

            result = process_candidate(
                path,
                job_analysis,
                options,
            )

            result["resumeUrl"] = (
                "/api/files/"
                f"{screening_id}/"
                f"{filename}"
            )

            candidates.append(result)

        # ----------------------------------------------------
        # STEP 4
        # ----------------------------------------------------

        update_screening(
            screening_id,

            currentStep="matchingSkills",

            progress=65,

            statusMessage=(
                "Matching candidate skills..."
            ),
        )

        # ----------------------------------------------------
        # STEP 5
        # ----------------------------------------------------

        update_screening(
            screening_id,

            currentStep="calculatingScore",

            progress=80,

            statusMessage=(
                "Calculating candidate scores..."
            ),
        )

        candidates.sort(
            key=lambda candidate:
                safe_float(
                    candidate.get(
                        "matchScore",
                        candidate.get(
                            "score",
                            0,
                        ),
                    )
                ),
            reverse=True,
        )

        # ----------------------------------------------------
        # STEP 6
        # ----------------------------------------------------

        update_screening(
            screening_id,

            currentStep="generatingExplanation",

            progress=92,

            statusMessage=(
                "Generating explanations..."
            ),
        )

        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        update_screening(
            screening_id,

            candidates=candidates,

            status="completed",

            progress=100,

            currentStep="completed",

            statusMessage=(
                "Screening completed successfully."
            ),

            completedAt=(
                datetime.utcnow().isoformat()
            ),
        )

        print("=" * 60)
        print(
            f"[SUCCESS] Screening "
            f"{screening_id} completed."
        )
        print(
            f"[SUCCESS] Candidates: "
            f"{len(candidates)}"
        )
        print("=" * 60)

    except Exception as exc:

        traceback.print_exc()

        update_screening(
            screening_id,

            status="error",

            currentStep="error",

            statusMessage=(
                f"Processing failed: {exc}"
            ),

            error=str(exc),
        )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "service": "ResumeAI Backend",
        "status": "running",
        "framework": "FastAPI",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "ResumeAI Backend",
        "framework": "FastAPI",
        "version": "3.0.0",
    }


# ============================================================
# CREATE SCREENING
# ============================================================

@app.post("/api/screenings")
def create_screening(
    data: CreateScreeningRequest,
):

    job_description = (
        data.jobDescription or ""
    ).strip()

    if not job_description:

        raise HTTPException(
            status_code=400,
            detail=(
                "Job description is required."
            ),
        )

    options = data.options

    if options is None:
        options = ScreeningOptions()

    screening_id = generate_id()

    screening = {

        "id": screening_id,

        "createdAt": (
            datetime.utcnow().isoformat()
        ),

        "jobDescription": job_description,

        "options": {

            "minMatchScore": (
                options.minMatchScore
            ),

            "skillSensitivity": (
                options.skillSensitivity
            ),

            "aiExplanation": (
                options.aiExplanation
            ),
        },

        "status": "created",

        "progress": 0,

        "currentStep": None,

        "statusMessage": (
            "Screening created."
        ),

        "error": None,

        "files": [],

        "candidates": [],

        "completedAt": None,
    }

    with lock:

        screenings[
            screening_id
        ] = screening

    print(
        f"[SCREENING CREATED] "
        f"{screening_id}"
    )

    return {
        "screeningId": screening_id
    }


# ============================================================
# UPLOAD RESUMES
# ============================================================

@app.post(
    "/api/screenings/{screening_id}/resumes"
)
async def upload_resumes(
    screening_id: str,
    background_tasks: BackgroundTasks,
    resumes: List[UploadFile] = File(...),
):

    with lock:

        screening = screenings.get(
            screening_id
        )

    if not screening:

        raise HTTPException(
            status_code=404,
            detail="Screening not found.",
        )

    if not resumes:

        raise HTTPException(
            status_code=400,
            detail=(
                "No resume files were uploaded."
            ),
        )

    screening_dir = (
        UPLOAD_DIR / screening_id
    )

    screening_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved_files = []

    for uploaded_file in resumes:

        if not uploaded_file.filename:
            continue

        original_name = Path(
            uploaded_file.filename
        ).name

        if not allowed_file(
            original_name
        ):

            print(
                f"[SKIPPED] Unsupported file: "
                f"{original_name}"
            )

            continue

        safe_name = re.sub(
            r"[^A-Za-z0-9._-]",
            "_",
            original_name,
        )

        unique_prefix = (
            uuid.uuid4().hex[:8]
        )

        stored_name = (
            f"{unique_prefix}_"
            f"{safe_name}"
        )

        save_path = (
            screening_dir / stored_name
        )

        try:

            content = await (
                uploaded_file.read()
            )

            if len(content) > MAX_FILE_BYTES:

                print(
                    f"[SKIPPED] File too large: "
                    f"{original_name}"
                )

                continue

            with open(
                save_path,
                "wb",
            ) as output_file:

                output_file.write(content)

            saved_files.append(
                {
                    "filename": stored_name,

                    "originalFilename":
                        original_name,

                    "path":
                        str(save_path),
                }
            )

            print(
                f"[UPLOADED] "
                f"{original_name}"
            )

        except Exception as exc:

            print(
                f"[UPLOAD ERROR] "
                f"{original_name}: "
                f"{exc}"
            )

    if not saved_files:

        raise HTTPException(
            status_code=400,
            detail={
                "message":
                    "No valid resume files were uploaded.",

                "allowedExtensions":
                    sorted(ALLOWED_EXTENSIONS),

                "maxFileSizeMB":
                    MAX_FILE_MB,
            },
        )

    update_screening(
        screening_id,

        files=saved_files,

        status="processing",

        progress=5,

        currentStep="uploadingCvs",

        statusMessage=(
            "Files uploaded. "
            "Starting screening..."
        ),
    )

    background_tasks.add_task(
        run_screening,
        screening_id,
    )

    return {
        "message":
            "Resumes uploaded successfully.",

        "screeningId":
            screening_id,

        "fileCount":
            len(saved_files),
    }


# ============================================================
# SCREENING STATUS
# ============================================================

@app.get(
    "/api/screenings/{screening_id}/status"
)
def screening_status(
    screening_id: str,
):

    with lock:

        screening = screenings.get(
            screening_id
        )

    if not screening:

        raise HTTPException(
            status_code=404,
            detail="Screening not found.",
        )

    return {

        "id":
            screening["id"],

        "status":
            screening["status"],

        "progress":
            screening["progress"],

        "currentStep":
            screening["currentStep"],

        "statusMessage":
            screening["statusMessage"],

        "error":
            screening["error"],

        "total":
            len(screening["files"]),

        "completed":
            len(screening["candidates"]),

        "createdAt":
            screening["createdAt"],

        "completedAt":
            screening["completedAt"],
    }


# ============================================================
# GET ONE CANDIDATE
# ============================================================

@app.get(
    "/api/screenings/{screening_id}/candidates/{index}"
)
def get_candidate(
    screening_id: str,
    index: int,
):

    with lock:

        screening = screenings.get(
            screening_id
        )

        if not screening:

            raise HTTPException(
                status_code=404,
                detail="Screening not found.",
            )

        candidates = list(
            screening["candidates"]
        )

    if (
        index < 0
        or index >= len(candidates)
    ):

        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    candidate = dict(
        candidates[index]
    )

    # Never expose raw resume text
    candidate.pop(
        "resumeText",
        None,
    )

    if "matchScore" not in candidate:

        candidate["matchScore"] = (
            safe_float(
                candidate.get(
                    "score",
                    0,
                )
            )
        )

    if "score" not in candidate:

        candidate["score"] = (
            candidate["matchScore"]
        )

    candidate["index"] = index

    candidate["total"] = len(
        candidates
    )

    return candidate


# ============================================================
# SUMMARY
# ============================================================

@app.get(
    "/api/screenings/{screening_id}/summary"
)
def get_summary(
    screening_id: str,
):

    with lock:

        screening = screenings.get(
            screening_id
        )

        if not screening:

            raise HTTPException(
                status_code=404,
                detail="Screening not found.",
            )

        candidates = list(
            screening["candidates"]
        )

        options = dict(
            screening["options"]
        )

    normalized_candidates = []

    for candidate in candidates:

        candidate_copy = dict(
            candidate
        )

        candidate_copy.pop(
            "resumeText",
            None,
        )

        score = safe_float(
            candidate_copy.get(
                "matchScore",
                candidate_copy.get(
                    "score",
                    0,
                ),
            )
        )

        candidate_copy["matchScore"] = round(
            clamp(score),
            1,
        )

        candidate_copy["score"] = (
            candidate_copy["matchScore"]
        )

        normalized_candidates.append(
            candidate_copy
        )

    normalized_candidates.sort(
        key=lambda candidate:
            safe_float(
                candidate.get(
                    "matchScore",
                    0,
                )
            ),
        reverse=True,
    )

    total = len(
        normalized_candidates
    )

    min_score = safe_float(
        options.get(
            "minMatchScore",
            60,
        ),
        60,
    )

    strong_matches = [
        candidate
        for candidate in normalized_candidates
        if safe_float(
            candidate.get(
                "matchScore",
                0,
            )
        ) >= min_score
    ]

    scores = [
        safe_float(
            candidate.get(
                "matchScore",
                0,
            )
        )
        for candidate
        in normalized_candidates
    ]

    average_match = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    top_candidate = (
        normalized_candidates[0]
        if normalized_candidates
        else None
    )

    top_match = (
        safe_float(
            top_candidate.get(
                "matchScore",
                0,
            )
        )
        if top_candidate
        else 0
    )

    return {

        "screeningId":
            screening_id,

        "status":
            screening["status"],

        "total":
            total,

        "totalCandidates":
            total,

        "strongMatches":
            len(strong_matches),

        "averageMatch":
            round(
                average_match,
                1,
            ),

        "topMatch":
            round(
                top_match,
                1,
            ),

        "topCandidate":
            {
                "name":
                    top_candidate.get(
                        "name",
                        "Unknown Candidate",
                    ),

                "score":
                    top_candidate.get(
                        "matchScore",
                        0,
                    ),

                "matchScore":
                    top_candidate.get(
                        "matchScore",
                        0,
                    ),

                "role":
                    top_candidate.get(
                        "role",
                        "Candidate",
                    ),
            }
            if top_candidate
            else None,

        "candidates":
            normalized_candidates,
    }


# ============================================================
# SERVE RESUME
# ============================================================

@app.get(
    "/api/files/{screening_id}/{filename:path}"
)
def serve_file(
    screening_id: str,
    filename: str,
):

    screening_dir = (
        UPLOAD_DIR / screening_id
    )

    if not screening_dir.exists():

        raise HTTPException(
            status_code=404,
            detail="Screening files not found.",
        )

    safe_filename = Path(
        filename
    ).name

    requested_file = (
        screening_dir / safe_filename
    )

    if not requested_file.exists():

        raise HTTPException(
            status_code=404,
            detail="Resume file not found.",
        )

    return FileResponse(
        path=str(
            requested_file
        ),
        filename=safe_filename,
        content_disposition_type="inline",
    )


# ============================================================
# LIST SCREENINGS
# ============================================================

@app.get(
    "/api/screenings"
)
def list_screenings():

    with lock:

        result = []

        for screening in screenings.values():

            result.append(
                {
                    "id":
                        screening["id"],

                    "createdAt":
                        screening["createdAt"],

                    "status":
                        screening["status"],

                    "progress":
                        screening["progress"],

                    "total":
                        len(
                            screening["files"]
                        ),

                    "completed":
                        len(
                            screening["candidates"]
                        ),
                }
            )

    result.sort(
        key=lambda item:
            item["createdAt"],
        reverse=True,
    )

    return {
        "screenings": result
    }


# ============================================================
# DELETE SCREENING
# ============================================================

@app.delete(
    "/api/screenings/{screening_id}"
)
def delete_screening(
    screening_id: str,
):

    with lock:

        if screening_id not in screenings:

            raise HTTPException(
                status_code=404,
                detail="Screening not found.",
            )

        del screenings[
            screening_id
        ]

    screening_dir = (
        UPLOAD_DIR / screening_id
    )

    if screening_dir.exists():

        for file in screening_dir.iterdir():

            try:

                if file.is_file():
                    file.unlink()

            except Exception:
                pass

        try:
            screening_dir.rmdir()
        except Exception:
            pass

    return {
        "message":
            "Screening deleted successfully.",

        "screeningId":
            screening_id,
    }


# ============================================================
# ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):

    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "message":
                "Internal server error.",

            "error":
                str(exc),
        },
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print("=" * 60)
    print("ResumeAI FastAPI Backend")
    print("=" * 60)

    print(
        f"Upload directory: {UPLOAD_DIR}"
    )

    print(
        "Allowed files:",
        ", ".join(
            sorted(
                ALLOWED_EXTENSIONS
            )
        ),
    )

    print(
        "Server: "
        "http://127.0.0.1:5000"
    )

    print(
        "Swagger: "
        "http://127.0.0.1:5000/docs"
    )

    print(
        "Health: "
        "http://127.0.0.1:5000/api/health"
    )

    print("=" * 60)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5000,
        reload=False,
    )