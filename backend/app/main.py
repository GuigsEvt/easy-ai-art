from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json

from app.routes import generate, stream

app = FastAPI(title="Easy AI Art API", description="AI Image Generation API", version="1.0.0")

# Get CORS origins from environment variable
cors_origins = os.getenv("CORS_ORIGINS", '["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"]')
try:
    cors_origins_list = json.loads(cors_origins)
except json.JSONDecodeError:
    cors_origins_list = ["http://localhost:8080", "http://localhost:3000", "http://localhost:5173"]

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated images statically
if os.path.exists("outputs"):
    app.mount("/images", StaticFiles(directory="outputs"), name="images")

# Include routes
app.include_router(generate.router, prefix="/api", tags=["generation"])
app.include_router(stream.router, prefix="/api", tags=["streaming"])

@app.get("/")
async def root():
    return {"message": "Easy AI Art API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8082"))
    uvicorn.run(app, host=host, port=port, reload=True)