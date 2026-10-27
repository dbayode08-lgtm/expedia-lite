"""Steady -- IST 402 Assignment 3 skills prototype (coursework only, not a support service).

Run from assignment3/backend:  uvicorn main:app --reload --port 8001
"""
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Model keys (if any) live in backend/.env (git-ignored, never committed).
load_dotenv(Path(__file__).parent / ".env")

from app.db import init_db  # noqa: E402
from app.routes import router  # noqa: E402

app = FastAPI(title="Steady (IST 402 A3 prototype)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def on_startup():
    init_db()
