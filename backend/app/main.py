from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
from dotenv import load_dotenv

from app.routes import generate, stream, models, auth
from app.core.auth import get_current_user

# Load environment variables
load_dotenv()

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
outputs_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
if os.path.exists(outputs_dir):
    app.mount("/images", StaticFiles(directory=outputs_dir), name="images")

# Include routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(generate.router, prefix="/api", tags=["generation"], dependencies=[Depends(get_current_user)])
app.include_router(stream.router, prefix="/api", tags=["streaming"], dependencies=[Depends(get_current_user)])
app.include_router(models.router, prefix="/api", tags=["models"], dependencies=[Depends(get_current_user)])

@app.get("/")
async def root(current_user: str = Depends(get_current_user)):
    return {"message": "Easy AI Art API is running!", "user": current_user}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8082"))
    uvicorn.run(app, host=host, port=port, reload=True)