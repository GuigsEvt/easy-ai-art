# Easy AI Art

A modern AI-powered image generation application with a React frontend and FastAPI backend.

> **🚨 DEVELOPMENT PROJECT NOTICE**
> 
> This project is designed for **local development and testing purposes only**. It includes basic authentication features that are **NOT production-ready**. Do not deploy this to production environments without implementing proper security measures.

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

### Environment Configuration

Before starting, copy the environment templates and configure your settings:

```bash
# Backend configuration
cd backend
cp .env.example .env
# Edit .env to customize authentication and API settings

# Frontend configuration  
cd ../frontend
cp .env.example .env
# Edit .env to match your backend configuration
```

### Option 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <YOUR_GIT_URL>
cd easy-ai-art

# Start both frontend and backend
docker compose up -d

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

# 0) (optional) recreate venv if things are messy
# python3 -m venv .venv && source .venv/bin/activate

pip install --upgrade pip setuptools wheel

# 1) Torch for macOS (MPS is included)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 2) The rest
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Backend runs on http://localhost:8000
```

## Testing the Uvicorn API Server

After setting up the backend, you can test the AI image generation API using the following methods:

### 1. Start the Server

```bash
cd backend

# Using virtual environment (recommended)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Or set PYTHONPATH if needed
PYTHONPATH=/path/to/backend python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. Test Endpoints

**Health Check:**
```bash
curl -X GET "http://localhost:8001/health"
# Expected response: {"status":"healthy"}
```

**List Available Models:**
```bash
curl -X GET "http://localhost:8001/api/models"
# Expected response: {"models":["sdxl-turbo"]}
```

**Generate an Image:**
```bash
curl -X POST "http://localhost:8001/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset over mountains",
    "width": 512,
    "height": 512,
    "num_inference_steps": 6,
    "guidance_scale": 1.0,
    "model_name": "sdxl-turbo"
  }'
```

**Generate with Advanced Parameters:**
```bash
curl -X POST "http://localhost:8001/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cute cat sitting in a garden",
    "negative_prompt": "blurry, low quality",
    "width": 512,
    "height": 512,
    "num_inference_steps": 8,
    "guidance_scale": 1.2,
    "seed": 42,
    "model_name": "sdxl-turbo"
  }'
```

### 3. API Response Format

Successful image generation returns:
```json
{
  "success": true,
  "image_url": "/images/sdxl_turbo_1762342632455.png",
  "message": "Image generated successfully",
  "filename": "sdxl_turbo_1762342632455.png",
  "generation_time": 15.6
}
```

### 4. Access Generated Images

Images are served statically at:
```
http://localhost:8001/images/{filename}
```

For example:
```bash
curl -I "http://localhost:8001/images/sdxl_turbo_1762342632455.png"
```

### 5. Interactive API Documentation

Visit the auto-generated docs:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### 6. Example Python Client

```python
import requests
import json

# Generate an image
response = requests.post(
    'http://localhost:8001/api/generate',
    headers={'Content-Type': 'application/json'},
    json={
        'prompt': 'a magical forest with glowing mushrooms',
        'width': 512,
        'height': 512,
        'num_inference_steps': 6,
        'guidance_scale': 1.0,
        'model_name': 'sdxl-turbo'
    }
)

result = response.json()
print(f"Generated image: {result['image_url']}")
print(f"Generation time: {result['generation_time']:.2f}s")
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

### Public Endpoints
- `GET /health` - Health check
- `GET /api/auth/auth-config` - Get authentication configuration

### Authentication Endpoints
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/logout` - Logout and clear session
- `GET /api/auth/auth-status` - Check authentication status

### Protected Endpoints (when AUTH_ENABLED=true)
- `GET /` - API root (shows user info)
- `POST /api/generate` - Generate AI image
- `GET /api/models` - List available models
- `GET /images/{filename}` - Serve generated images

## Authentication

Easy AI Art supports optional cookie-based authentication. Authentication can be enabled or disabled via environment variables.

> **⚠️ IMPORTANT SECURITY WARNING**
> 
> The authentication system included in this project is designed for **development and testing purposes only**. It is **NOT suitable for production use** due to:
> - Simple in-memory session storage (sessions lost on server restart)
> - Basic username/password authentication without encryption
> - Default credentials are publicly known
> - No rate limiting or brute force protection
> - No password complexity requirements
> - Sessions stored in plain HTTP cookies (not encrypted)
> 
> **For production deployments**, implement proper authentication with:
> - Database-backed session storage (Redis/PostgreSQL)
> - Encrypted passwords with proper salting
> - JWT tokens or OAuth2 integration
> - HTTPS/SSL encryption
> - Rate limiting and security monitoring
> - Strong password policies

### Configuration

Set these variables in your `backend/.env` file:

```bash
# Enable/disable authentication (DEVELOPMENT/TESTING ONLY)
AUTH_ENABLED=false  # Set to true to require login

# Default credentials (CHANGE THESE - NOT FOR PRODUCTION!)
AUTH_USERNAME=admin
AUTH_PASSWORD=admin123

# Session duration in hours (how long users stay logged in)
SESSION_DURATION_HOURS=24  # 1 day default
```

> **🔧 Development Use Only**: These credentials are intended for local development and testing. Never use these default values or this authentication system in any production environment.

### Frontend Configuration

For the frontend, add to `frontend/.env`:

```bash
# Tell frontend whether auth is enabled
VITE_AUTH_ENABLED=false

# Backend API URL
VITE_API_URL=http://localhost:8082
```

### Using Authentication

**When AUTH_ENABLED=false:**
- All endpoints work without authentication
- No login required

**When AUTH_ENABLED=true:**
- Login required for most endpoints
- Use session cookies for subsequent requests

**Login Example:**
```bash
# Login and save cookies
curl -X POST "http://localhost:8082/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  -c cookies.txt

# Use session cookie for authenticated requests
curl -X GET "http://localhost:8082/api/models" -b cookies.txt

# Logout
curl -X POST "http://localhost:8082/api/auth/logout" -b cookies.txt
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

**Backend (`backend/.env`):**
- `AUTH_ENABLED` - Enable/disable authentication (true/false) - **Development only**
- `AUTH_USERNAME` - Login username (default: admin) - **Not for production**
- `AUTH_PASSWORD` - Login password (default: admin123) - **Not for production**
- `SESSION_DURATION_HOURS` - How long sessions last in hours (default: 24)
- `API_HOST`, `API_PORT` - Server configuration
- `CORS_ORIGINS` - Allowed frontend origins

**Frontend (`frontend/.env`):**
- `VITE_AUTH_ENABLED` - Whether frontend should show login (true/false)
- `VITE_API_URL` - Backend API URL

## Adding AI Models

1. Uncomment AI dependencies in `backend/requirements.txt`
2. Install: `pip install torch diffusers transformers`
3. Download models using Hugging Face CLI:
```bash
huggingface-cli download stabilityai/sdxl-turbo \
  --local-dir ./backend/models/sdxl-turbo \
  --local-dir-use-symlinks False
```
4. Update `backend/app/core/pipeline.py` with actual model implementation

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS
