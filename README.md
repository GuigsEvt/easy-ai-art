# Easy AI Art

A modern AI-powered image generation application with a React frontend and FastAPI backend.

## Architecture

```
easy-ai-art/
├── frontend/               # React/Vite frontend
├── backend/                # FastAPI backend for AI models  
├── .env                    # Environment configuration
├── docker-compose.yml      # Development setup
└── README.md
```

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <YOUR_GIT_URL>
cd easy-ai-art

# Start both frontend and backend
docker-compose up -d

# Frontend: http://localhost:8080
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:8080
```

**Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Backend runs on http://localhost:8000
```

## Development

**Frontend (React + Vite):**
- Located in `frontend/`
- Built with React, TypeScript, Tailwind CSS
- UI components from shadcn/ui
- Proxy configured to backend API

**Backend (FastAPI):**
- Located in `backend/`
- RESTful API for AI image generation
- Pydantic models for request/response validation
- Structured with routes, core utilities, and models

## API Endpoints

- `GET /` - Health check
- `POST /api/generate` - Generate AI image
- `GET /api/models` - List available models
- `GET /images/{filename}` - Serve generated images

## Environment Variables

Copy `.env.example` to `.env` and configure:

**Frontend:**
- `VITE_API_BASE_URL` - Backend API URL
- `VITE_SUPABASE_*` - Supabase configuration

**Backend:**
- `API_HOST`, `API_PORT` - Server configuration
- `DEFAULT_MODEL` - AI model to use
- `MODELS_CACHE_DIR` - Model storage directory

## Adding AI Models

1. Uncomment AI dependencies in `backend/requirements.txt`
2. Install: `pip install torch diffusers transformers`
3. Update `backend/app/core/pipeline.py` with actual model implementation

## Project Info

**URL**: https://lovable.dev/projects/a45a1a4c-5327-47ce-86ca-82c68bfb06e9
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS
