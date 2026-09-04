from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import auth as auth_router, buildings, meetings, votes, companies, documents

# Kreira tabele u bazi ako ne postoje (za produkciju se preporucuje Alembic za migracije)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kucni Savet API", version="1.0.0")

# CORS - dozvoljava frontend-u da prica sa backend-om
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # U produkciji: zameniti sa tacnim frontend URL-om
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(companies.router)
app.include_router(buildings.router)
app.include_router(meetings.router)
app.include_router(votes.router)
app.include_router(documents.router)


@app.get("/health")
def health_check():
    """Koristi ALB/Render health check da proveri da li je servis ziv"""
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Kucni Savet API radi"}
