from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Finance App API",
    version="1.0.0",
    description="Személyes pénzügyi elemző alkalmazás",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Finance App API v1.0", "status": "running"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
    )
