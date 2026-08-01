"""Einstiegspunkt der FastAPI-Anwendung."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes import router


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="SSH Sentinel Mini-SIEM",
    description="Demo-Analyse von SSH-Authentifizierungslogs für eine Modularbeit.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)
