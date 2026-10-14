"""
FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Backend API",
    description="Python backend for the monorepo project",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Backend API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "environment": "staging"}


@app.get("/api/health")
async def api_health():
    """API health check"""
    return {"status": "healthy", "service": "backend"}


@app.get("/api/data")
async def get_data():
    """Sample data endpoint"""
    return {
        "data": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
    }
