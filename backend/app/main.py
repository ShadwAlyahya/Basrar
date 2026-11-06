from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api import auth, datasets, analysis

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Basrar AI Data Analytics Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analysis.router)

@app.get("/")
def root():
    return {"message": "Welcome to Basrar API - System is fully running!"}