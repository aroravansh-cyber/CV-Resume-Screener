from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(
    title = "Hackathon AI API",
    description="Hackathon backend",
    version="1.0.0"
)

#cros = croos origin resources sharing

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message":"Hackathon Ai Backend is running"
    }

@app.get("/api/health",tags=["Health"])
def health():
    return {
        "status": "healthy",
        "message": "backend is running"
    }