# ============================================================
# ResumeAI - FastAPI Backend
# Complete replacement for main.py
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
import os


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
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None


# ============================================================
# APP CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MAX_FILE_MB = 10

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "jpg",
    "jpeg",
    "png",
}


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="ResumeAI API",
    description=(
        "AI-powered CV / Resume Screening API"
    ),
    version="1.0.0",
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
# IN-MEMORY DATABASE
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

    # Databases
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

    # Cloud / DevOps
    "aws",
    "amazon web services",
    "azure",
    "google cloud",
    "gcp",
    "docker",
    "kubernetes",
    "linux",
    "bash",
    "jenkins",
    "ci/cd",

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

    # Data
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

    # Git
    "git",
    "github",
    "gitlab",

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
# ROLE KEYWORDS
# ============================================================

ROLE_KEYWORDS = {
    "software engineer": [
        "software engineer",
        "software developer",
        "software development",
        "backend developer",
        "frontend developer",
        "full stack developer",
        "full-stack developer",
    ],

    "data scientist": [
        "data scientist",
        "data science",
        "machine learning",
        "statistics",
        "predictive modeling",
    ],

    "machine learning engineer": [
        "machine learning engineer",
        "machine learning",
        "ml engineer",
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
# UTILITY FUNCTIONS
# ============================================================

def generate_id() -> str:
    return uuid.uuid4().hex[:12]


def allowed_file(filename: str) -> bool:
    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def get_extension(filename: str) -> str:
    if "." not in filename:
        return ""

    return filename.rsplit(
        ".",
        1
    )[1].lower()


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"\r\n?",
        "\n",
        text
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def normalize_for_search(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    text = text.replace(
        "–",
        "-"
    )

    text = text.replace(
        "—",
        "-"
    )

    return text


def safe_float(
    value,
    default=0
) -> float:

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return default


def clamp(
    value,
    minimum=0,
    maximum=100
):
    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_text(
    file_path: Path
) -> str:

    if PdfReader is None:
        return ""

    try:
        reader = PdfReader(
            str(file_path)
        )

        pages = []

        for page in reader.pages:

            try:
                text = (
                    page.extract_text()
                    or ""
                )

                pages.append(text)

            except Exception:
                continue

        return clean_text(
            "\n".join(pages)
        )

    except Exception as exc:

        print(
            f"[PDF ERROR] {exc}"
        )

        return ""


# ============================================================
# DOCX EXTRACTION
# ============================================================

def extract_docx_text(
    file_path: Path
) -> str:

    if Document is None:
        return ""

    try:
        document = Document(
            str(file_path)
        )

        parts = []

        for paragraph in document.paragraphs:

            if paragraph.text:
                parts.append(
                    paragraph.text
                )

        # Tables
        for table in document.tables:

            for row in table.rows:

                values = []

                for cell in row.cells:

                    if cell.text:
                        values.append(
                            cell.text
                        )

                if values:
                    parts.append(
                        " | ".join(values)
                    )

        return clean_text(
            "\n".join(parts)
        )

    except Exception as exc:

        print(
            f"[DOCX ERROR] {exc}"
        )

        return ""


# ============================================================
# DOC EXTRACTION
# ============================================================

def extract_doc_text(
    file_path: Path
) -> str:

    try:

        result = subprocess.run(
            [
                "antiword",
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=20
        )

        if result.returncode == 0:

            return clean_text(
                result.stdout
            )

    except Exception:
        pass

    return ""


# ============================================================
# IMAGE OCR
# ============================================================

def extract_image_text(
    file_path: Path
) -> str:

    if (
        Image is None
        or pytesseract is None
    ):
        return ""

    try:

        image = Image.open(
            file_path
        )

        text = pytesseract.image_to_string(
            image
        )

        return clean_text(
            text
        )

    except Exception as exc:

        print(
            f"[OCR ERROR] {exc}"
        )

        return ""


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_resume_text(
    file_path: Path
) -> str:

    extension = get_extension(
        file_path.name
    )

    if extension == "pdf":
        return extract_pdf_text(
            file_path
        )

    if extension == "docx":
        return extract_docx_text(
            file_path
        )

    if extension == "doc":
        return extract_doc_text(
            file_path
        )

    if extension in {
        "jpg",
        "jpeg",
        "png"
    }:
        return extract_image_text(
            file_path
        )

    return ""


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(
    text: str
) -> List[str]:

    normalized = normalize_for_search(
        text
    )

    found = set()

    skills = sorted(
        SKILL_DATABASE,
        key=len,
        reverse=True
    )

    for skill in skills:

        normalized_skill = (
            normalize_for_search(
                skill
            )
        )

        if not normalized_skill:
            continue

        pattern = (
            r"(?<![a-z0-9+#])"
            + re.escape(
                normalized_skill
            )
            + r"(?![a-z0-9+#])"
        )

        try:

            if re.search(
                pattern,
                normalized
            ):
                found.add(skill)

        except re.error:

            if normalized_skill in normalized:
                found.add(skill)

    return sorted(found)


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name(
    text: str,
    filename: str = ""
) -> str:

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Explicit name
    for line in lines[:20]:

        match = re.match(
            r"^(?:name|candidate name)"
            r"\s*[:\-]\s*(.+)$",
            line,
            re.IGNORECASE
        )

        if match:

            name = (
                match.group(1)
                .strip()
            )

            if 2 <= len(
                name.split()
            ) <= 6:

                return name

    blocked_words = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "summary",
        "objective",
        "experience",
        "education",
        "skills",
        "contact",
        "email",
        "phone",
        "developer",
        "engineer",
    }

    for line in lines[:12]:

        clean = re.sub(
            r"[^A-Za-z .'-]",
            "",
            line
        ).strip()

        words = clean.split()

        if not words:
            continue

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

        if all(
            re.match(
                r"^[A-Za-z][A-Za-z.'-]*$",
                word
            )
            for word in words
        ):
            return clean

    # Filename fallback
    if filename:

        stem = Path(
            filename
        ).stem

        stem = re.sub(
            r"[_\-]+",
            " ",
            stem
        )

        stem = re.sub(
            r"\b(resume|cv|final|updated|new)\b",
            "",
            stem,
            flags=re.IGNORECASE
        )

        stem = re.sub(
            r"\s+",
            " ",
            stem
        ).strip()

        if stem:
            return stem.title()

    return "Unknown Candidate"


# ============================================================
# LOCATION EXTRACTION
# ============================================================

def extract_location(
    text: str
) -> str:

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
            re.IGNORECASE
        )

        if match:

            value = (
                match.group(1)
                .strip()
            )

            value = re.sub(
                r"\s{2,}",
                " ",
                value
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

def extract_experience(
    text: str
) -> str:

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*"
        r"(?:years?|yrs?)\s*"
        r"(?:of)?\s*experience",

        r"experience\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\+?\s*"
        r"(?:years?|yrs?)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            years = safe_float(
                match.group(1),
                0
            )

            if years == int(years):

                return (
                    f"{int(years)} years"
                )

            return (
                f"{years:g} years"
            )

    if re.search(
        r"\bintern(ship)?\b",
        text,
        re.IGNORECASE
    ):
        return "Internship experience"

    return "Not specified"


# ============================================================
# ROLE EXTRACTION
# ============================================================

def extract_role(
    text: str
) -> str:

    normalized = normalize_for_search(
        text
    )

    for role, keywords in ROLE_KEYWORDS.items():

        for keyword in keywords:

            if normalize_for_search(
                keyword
            ) in normalized:

                return role.title()

    return "Candidate"


# ============================================================
# EMAIL EXTRACTION
# ============================================================

def extract_email(
    text: str
) -> str:

    match = re.search(
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}\b",
        text
    )

    if match:
        return match.group(0)

    return ""


# ============================================================
# PHONE EXTRACTION
# ============================================================

def extract_phone(
    text: str
) -> str:

    match = re.search(
        r"(?<!\d)"
        r"(?:\+91[\s-]?)?"
        r"[6-9]\d{9}"
        r"(?!\d)",
        text
    )

    if match:
        return match.group(0)

    return ""


# ============================================================
# JOB DESCRIPTION ANALYSIS
# ============================================================

def analyze_job_description(
    job_description: str
) -> Dict[str, Any]:

    skills = extract_skills(
        job_description
    )

    role = extract_role(
        job_description
    )

    return {
        "skills": skills,
        "role": role,
        "skillCount": len(skills),
    }


# ============================================================
# CANDIDATE ANALYSIS
# ============================================================

def analyze_candidate(
    resume_text: str,
    filename: str
) -> Dict[str, Any]:

    skills = extract_skills(
        resume_text
    )

    return {
        "name": extract_name(
            resume_text,
            filename
        ),

        "role": extract_role(
            resume_text
        ),

        "experience": extract_experience(
            resume_text
        ),

        "location": extract_location(
            resume_text
        ),

        "email": extract_email(
            resume_text
        ),

        "phone": extract_phone(
            resume_text
        ),

        "skills": skills,
    }


# ============================================================
# SKILL MATCHING
# ============================================================

def calculate_skill_match(
    jd_skills: List[str],
    candidate_skills: List[str],
    sensitivity: str = "balanced"
) -> Dict[str, Any]:

    jd_set = {
        normalize_for_search(
            skill
        )
        for skill in jd_skills
    }

    candidate_set = {
        normalize_for_search(
            skill
        )
        for skill in candidate_skills
    }

    if not jd_set:

        return {
            "score": 50,
            "matched": [],
            "missing": [],
        }

    matched_normalized = (
        jd_set.intersection(
            candidate_set
        )
    )

    missing_normalized = (
        jd_set.difference(
            candidate_set
        )
    )

    skill_map = {
        normalize_for_search(skill): skill
        for skill in jd_skills
    }

    matched = [
        skill_map[item]
        for item in matched_normalized
        if item in skill_map
    ]

    missing = [
        skill_map[item]
        for item in missing_normalized
        if item in skill_map
    ]

    score = (
        len(matched)
        / len(jd_set)
    ) * 100

    sensitivity = str(
        sensitivity or "balanced"
    ).lower()

    if sensitivity == "strict":

        score *= 0.95

    elif sensitivity == "flexible":

        score = min(
            100,
            score * 1.05 + 3
        )

    return {
        "score": clamp(
            round(score, 1)
        ),

        "matched": sorted(
            matched
        ),

        "missing": sorted(
            missing
        ),
    }


# ============================================================
# EXPERIENCE SCORE
# ============================================================

def calculate_experience_score(
    job_description: str,
    resume_text: str
) -> float:

    jd_lower = normalize_for_search(
        job_description
    )

    resume_lower = normalize_for_search(
        resume_text
    )

    required_match = re.search(
        r"(\d+(?:\.\d+)?)\+?\s*"
        r"(?:years?|yrs?)",
        jd_lower
    )

    candidate_match = re.search(
        r"(\d+(?:\.\d+)?)\+?\s*"
        r"(?:years?|yrs?)",
        resume_lower
    )

    if not required_match:
        return 100

    required_years = safe_float(
        required_match.group(1),
        0
    )

    candidate_years = (
        safe_float(
            candidate_match.group(1),
            0
        )
        if candidate_match
        else 0
    )

    if required_years <= 0:
        return 100

    if candidate_years >= required_years:
        return 100

    ratio = (
        candidate_years
        / required_years
    )

    return clamp(
        round(
            ratio * 100,
            1
        )
    )


# ============================================================
# FINAL SCORE
# ============================================================

def calculate_final_score(
    skill_score: float,
    experience_score: float
) -> float:

    score = (
        skill_score * 0.85
        + experience_score * 0.15
    )

    return clamp(
        round(score, 1)
    )


# ============================================================
# EXPLANATION
# ============================================================

def generate_explanation(
    candidate: Dict[str, Any],
    job_analysis: Dict[str, Any],
    match_result: Dict[str, Any],
    final_score: float
) -> str:

    matched = match_result[
        "matched"
    ]

    missing = match_result[
        "missing"
    ]

    jd_skills = job_analysis[
        "skills"
    ]

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
    options: Dict[str, Any]
) -> Dict[str, Any]:

    filename = file_path.name

    resume_text = extract_resume_text(
        file_path
    )

    candidate = analyze_candidate(
        resume_text,
        filename
    )

    match_result = calculate_skill_match(
        job_analysis["skills"],
        candidate["skills"],
        options.get(
            "skillSensitivity",
            "balanced"
        )
    )

    experience_score = (
        calculate_experience_score(
            options.get(
                "jobDescription",
                ""
            ),
            resume_text
        )
    )

    final_score = calculate_final_score(
        match_result["score"],
        experience_score
    )

    explanation = generate_explanation(
        candidate,
        job_analysis,
        match_result,
        final_score
    )

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

        "skillScore": (
            match_result["score"]
        ),

        "experienceScore": (
            experience_score
        ),

        "score": final_score,

        "explanation": explanation,

        "resumeFilename": filename,

        "resumeUrl": None,

        # Internal field
        "resumeText": resume_text,
    }


# ============================================================
# UPDATE PROCESSING STATUS
# ============================================================

def update_screening(
    screening_id: str,
    **values
):

    with lock:

        screening = screenings.get(
            screening_id
        )

        if not screening:
            return

        screening.update(
            values
        )


# ============================================================
# BACKGROUND SCREENING
# ============================================================

def run_screening(
    screening_id: str
):

    try:

        with lock:

            screening = screenings.get(
                screening_id
            )

            if not screening:
                return

            job_description = (
                screening[
                    "jobDescription"
                ]
            )

            options = dict(
                screening[
                    "options"
                ]
            )

            files = list(
                screening[
                    "files"
                ]
            )

        # ----------------------------------------------------
        # STEP 1
        # ----------------------------------------------------

        update_screening(
            screening_id,
            currentStep=(
                "readingJobDescription"
            ),
            progress=10,
            statusMessage=(
                "Reading job description..."
            )
        )

        job_analysis = (
            analyze_job_description(
                job_description
            )
        )

        options[
            "jobDescription"
        ] = job_description

        # ----------------------------------------------------
        # STEP 2
        # ----------------------------------------------------

        update_screening(
            screening_id,
            currentStep="uploadingCvs",
            progress=25,
            statusMessage=(
                "Preparing resumes..."
            )
        )

        # ----------------------------------------------------
        # STEP 3
        # ----------------------------------------------------

        candidates = []

        total_files = len(files)

        for index, file_info in enumerate(
            files
        ):

            filename = file_info[
                "filename"
            ]

            path = Path(
                file_info["path"]
            )

            progress = (
                30
                + (
                    (
                        index + 1
                    )
                    / max(
                        total_files,
                        1
                    )
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
                )
            )

            result = process_candidate(
                path,
                job_analysis,
                options
            )

            result[
                "resumeUrl"
            ] = (
                "/api/files/"
                f"{screening_id}/"
                f"{filename}"
            )

            candidates.append(
                result
            )

        # ----------------------------------------------------
        # STEP 4
        # ----------------------------------------------------

        update_screening(
            screening_id,
            currentStep="matchingSkills",
            progress=65,
            statusMessage=(
                "Matching candidate skills..."
            )
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
            )
        )

        candidates.sort(
            key=lambda candidate:
                candidate.get(
                    "score",
                    0
                ),
            reverse=True
        )

        # ----------------------------------------------------
        # STEP 6
        # ----------------------------------------------------

        update_screening(
            screening_id,
            currentStep=(
                "generatingExplanation"
            ),
            progress=92,
            statusMessage=(
                "Generating explanations..."
            )
        )

        # Explanations were already
        # generated for each candidate.

        # ----------------------------------------------------
        # FINISH
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
                datetime.utcnow()
                .isoformat()
            )
        )

        print(
            f"[SUCCESS] Screening "
            f"{screening_id} completed."
        )

    except Exception as exc:

        traceback.print_exc()

        update_screening(
            screening_id,

            status="error",

            currentStep="error",

            statusMessage=(
                f"Processing failed: {exc}"
            ),

            error=str(exc)
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
        "version": "1.0.0",
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
        "version": "1.0.0",
    }


# ============================================================
# CREATE SCREENING
# ============================================================

@app.post("/api/screenings")
def create_screening(
    data: CreateScreeningRequest
):

    job_description = (
        data.jobDescription
        or ""
    ).strip()

    if not job_description:

        raise HTTPException(
            status_code=400,
            detail=(
                "Job description is required."
            )
        )

    options = data.options

    if options is None:

        options = ScreeningOptions()

    screening_id = generate_id()

    screening = {
        "id": screening_id,

        "createdAt": (
            datetime.utcnow()
            .isoformat()
        ),

        "jobDescription": (
            job_description
        ),

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
    resumes: List[UploadFile] = File(...)
):

    with lock:

        screening = screenings.get(
            screening_id
        )

    if not screening:

        raise HTTPException(
            status_code=404,
            detail=(
                "Screening not found."
            )
        )

    if not resumes:

        raise HTTPException(
            status_code=400,
            detail=(
                "No resume files were uploaded."
            )
        )

    screening_dir = (
        UPLOAD_DIR / screening_id
    )

    screening_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    saved_files = []

    for uploaded_file in resumes:

        if not uploaded_file.filename:
            continue

        original_name = (
            Path(
                uploaded_file.filename
            ).name
        )

        if not allowed_file(
            original_name
        ):
            continue

        # Make filename safe
        safe_name = re.sub(
            r"[^A-Za-z0-9._-]",
            "_",
            original_name
        )

        unique_prefix = (
            uuid.uuid4().hex[:8]
        )

        stored_name = (
            f"{unique_prefix}_"
            f"{safe_name}"
        )

        save_path = (
            screening_dir
            / stored_name
        )

        try:

            content = await (
                uploaded_file.read()
            )

            # Per-file size check
            max_bytes = (
                MAX_FILE_MB
                * 1024
                * 1024
            )

            if len(content) > max_bytes:

                continue

            with open(
                save_path,
                "wb"
            ) as output_file:

                output_file.write(
                    content
                )

            saved_files.append(
                {
                    "filename": (
                        stored_name
                    ),

                    "originalFilename": (
                        original_name
                    ),

                    "path": str(
                        save_path
                    ),
                }
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
                "message": (
                    "No valid resume files "
                    "were uploaded."
                ),

                "allowedExtensions": sorted(
                    ALLOWED_EXTENSIONS
                ),

                "maxFileSizeMB": (
                    MAX_FILE_MB
                ),
            }
        )

    update_screening(
        screening_id,

        files=saved_files,

        status="processing",

        progress=5,

        currentStep=(
            "uploadingCvs"
        ),

        statusMessage=(
            "Files uploaded. "
            "Starting screening..."
        )
    )

    # Start processing
    background_tasks.add_task(
        run_screening,
        screening_id
    )

    return {
        "message": (
            "Resumes uploaded successfully."
        ),

        "screeningId": screening_id,

        "fileCount": len(
            saved_files
        ),
    }


# ============================================================
# SCREENING STATUS
# ============================================================

@app.get(
    "/api/screenings/{screening_id}/status"
)
def screening_status(
    screening_id: str
):

    with lock:

        screening = screenings.get(
            screening_id
        )

    if not screening:

        raise HTTPException(
            status_code=404,
            detail=(
                "Screening not found."
            )
        )

    return {
        "id": screening["id"],

        "status": screening[
            "status"
        ],

        "progress": screening[
            "progress"
        ],

        "currentStep": screening[
            "currentStep"
        ],

        "statusMessage": screening[
            "statusMessage"
        ],

        "error": screening[
            "error"
        ],

        "total": len(
            screening["files"]
        ),

        "completed": len(
            screening["candidates"]
        ),

        "createdAt": screening[
            "createdAt"
        ],

        "completedAt": screening[
            "completedAt"
        ],
    }


# ============================================================
# GET CANDIDATE
# ============================================================

@app.get(
    "/api/screenings/{screening_id}/candidates/{index}"
)
def get_candidate(
    screening_id: str,
    index: int
):

    with lock:

        screening = screenings.get(
            screening_id
        )

        if not screening:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Screening not found."
                )
            )

        candidates = list(
            screening[
                "candidates"
            ]
        )

    if (
        index < 0
        or index >= len(candidates)
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Candidate not found."
            )
        )

    candidate = dict(
        candidates[index]
    )

    # Don't expose full resume text
    candidate.pop(
        "resumeText",
        None
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
    screening_id: str
):

    with lock:

        screening = screenings.get(
            screening_id
        )

        if not screening:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Screening not found."
                )
            )

        candidates = list(
            screening[
                "candidates"
            ]
        )

        options = dict(
            screening[
                "options"
            ]
        )

    total = len(
        candidates
    )

    min_score = safe_float(
        options.get(
            "minMatchScore",
            60
        ),
        60
    )

    strong_matches = [
        candidate
        for candidate in candidates
        if safe_float(
            candidate.get(
                "score",
                0
            )
        ) >= min_score
    ]

    scores = [
        safe_float(
            candidate.get(
                "score",
                0
            )
        )
        for candidate in candidates
    ]

    average_match = (
        sum(scores) / len(scores)
        if scores
        else 0
    )

    sorted_candidates = sorted(
        candidates,
        key=lambda candidate:
            safe_float(
                candidate.get(
                    "score",
                    0
                )
            ),
        reverse=True
    )

    top_candidate = (
        sorted_candidates[0]
        if sorted_candidates
        else None
    )

    result_candidates = []

    for candidate in sorted_candidates:

        clean_candidate = dict(
            candidate
        )

        clean_candidate.pop(
            "resumeText",
            None
        )

        result_candidates.append(
            clean_candidate
        )

    return {
        "screeningId": screening_id,

        "status": screening[
            "status"
        ],

        "total": total,

        "strongMatches": len(
            strong_matches
        ),

        "averageMatch": round(
            average_match,
            1
        ),

        "topMatch": (
            round(
                safe_float(
                    top_candidate.get(
                        "score",
                        0
                    )
                ),
                1
            )
            if top_candidate
            else 0
        ),

        "topCandidate": (
            {
                "name": (
                    top_candidate.get(
                        "name",
                        "Unknown Candidate"
                    )
                ),

                "score": (
                    top_candidate.get(
                        "score",
                        0
                    )
                ),

                "role": (
                    top_candidate.get(
                        "role",
                        "Candidate"
                    )
                ),
            }
            if top_candidate
            else None
        ),

        "candidates": (
            result_candidates
        ),
    }


# ============================================================
# SERVE RESUME FILE
# ============================================================

@app.get(
    "/api/files/{screening_id}/{filename:path}"
)
def serve_file(
    screening_id: str,
    filename: str
):

    screening_dir = (
        UPLOAD_DIR / screening_id
    )

    if not screening_dir.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Screening files not found."
            )
        )

    # Security: only use the file's name,
    # preventing ../ path traversal.
    safe_filename = Path(
        filename
    ).name

    requested_file = (
        screening_dir
        / safe_filename
    )

    if not requested_file.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Resume file not found."
            )
        )

    return FileResponse(
        path=str(
            requested_file
        ),
        filename=safe_filename,
        content_disposition_type="inline"
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
                    "id": screening[
                        "id"
                    ],

                    "createdAt": screening[
                        "createdAt"
                    ],

                    "status": screening[
                        "status"
                    ],

                    "progress": screening[
                        "progress"
                    ],

                    "total": len(
                        screening[
                            "files"
                        ]
                    ),

                    "completed": len(
                        screening[
                            "candidates"
                        ]
                    ),
                }
            )

    result.sort(
        key=lambda item:
            item["createdAt"],
        reverse=True
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
    screening_id: str
):

    with lock:

        if screening_id not in screenings:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Screening not found."
                )
            )

        del screenings[
            screening_id
        ]

    # Delete uploaded files
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
        "message": (
            "Screening deleted successfully."
        ),

        "screeningId": screening_id,
    }


# ============================================================
# GLOBAL ERROR HANDLER
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "message": (
                "Internal server error."
            ),

            "error": str(exc),
        }
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
        )
    )

    print(
        "Server: "
        "http://127.0.0.1:5000"
    )

    print(
        "Swagger Docs: "
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
    reload=False
)