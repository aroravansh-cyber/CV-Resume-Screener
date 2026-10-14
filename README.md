# 📄 CV Resume Screener

An AI-powered resume screening system that helps recruiters upload CVs, screen candidates and view summaries in one place.

![Recognition](https://img.shields.io/badge/🏆_1st_Runner--Up-AI--Buildthon_2.0-brightgreen?style=for-the-badge)

```diff
+ 🏆 1st Runner-Up, AI-Buildthon 2.0, GRD IMT Dehradun
```

---

## 📌 About the Project

CV Resume Screener lets a user upload resumes, screen candidates automatically and review the results through a simple web interface. The project has a **Python backend** that handles resume uploads and processing, and a **frontend** built with HTML, CSS and vanilla JavaScript.

## ✨ Features

- Upload resumes through the web interface
- Candidate listing and candidate detail view
- Resume screening with results
- Summary page for screening outcomes
- Settings page to configure the screening
- Clean, responsive UI

> Edit this list so it matches exactly what your project does.

## 🛠️ Tech Stack

| Layer    | Technology                                   |
|----------|----------------------------------------------|
| Frontend | HTML, CSS, Vanilla JavaScript                |
| Backend  | Python ([FastAPI / Flask – update this])     |
| AI / ML  | [Add model / library used, e.g. spaCy, scikit-learn, LLM API] |

## 📁 Project Structure

```
CV-Resume-Screener/
├── backend/
│   └── app/
│       ├── main.py          # Backend entry point
│       └── uploads/         # Uploaded resumes
├── frontend/
│   ├── index.html           # Home / upload page
│   ├── candidate.html       # Candidate details
│   ├── screening.html       # Screening page
│   ├── summary.html         # Screening summary
│   ├── settings.html        # Settings
│   ├── script.js            # Frontend logic
│   ├── style.css            # Styling
│   └── README.md
└── README.md
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<owner>/CV-Resume-Screener.git
cd CV-Resume-Screener
```

### 2. Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> Use the command that matches your framework (for Flask: `python app/main.py`).

### 3. Run the frontend

Open `frontend/index.html` in your browser, or use VS Code Live Server.

## 🏆 Recognition

- **1st Runner-Up** at **AI-Buildthon 2.0**, GRD Uttarakhand University Dehradun (2026)

## 🔮 Future Improvements

- Bulk resume upload and ranking
- Better skill extraction and job-description matching
- Export screening reports
- User login and saved sessions

## 👥 Team

- [Vansh Aroa](https://github.com/aroravansh-cyber) – Team Lead, Frontend Lead
- [Nitin Singh](https://github.com/nitinsingh-06) – Backend Lead & Developer
- [Ayushi Panwar](https://github.com/Ayushi5491) – Frontend Developer
- [Akash Anthwal](https://github.com/akashanthwal99-max) – Documentaion

## 📄 License

This project is licensed under the MIT License.
