from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.routes import generate

app = FastAPI(title="Easy AI Art API", description="AI Image Generation API", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite/React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated images statically
if os.path.exists("outputs"):
    app.mount("/images", StaticFiles(directory="outputs"), name="images")

# Include routes
app.include_router(generate.router, prefix="/api", tags=["generation"])

@app.get("/")
async def root():
    return {"message": "Easy AI Art API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)