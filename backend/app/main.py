from fastapi import FastAPI
from app.core.database import engine, Base
from app.api import auth, datasets, analysis

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Basrar AI Data Analytics Platform",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analysis.router)

@app.get("/")
def root():
    return {"message": "Welcome to Basrar API - System is fully running!"}