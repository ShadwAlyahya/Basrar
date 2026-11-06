from fastapi import FastAPI

# Initialize Basrar FastAPI Application
app = FastAPI(
    title="Basrar API",
    description="AI-Powered Autonomous Data Analyst Backend",
    version="1.0.0"
)

# Root Endpoint
@app.get("/")
def read_root():
    return {
        "system": "Basrar",
        "status": "Active",
        "message": "Welcome to the AI-Powered Autonomous Data Analyst platform."
    }

# Health Check Endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}