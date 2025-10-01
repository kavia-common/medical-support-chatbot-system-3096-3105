# Backend Setup (FastAPI)

This document explains how to run the backend for the CrewAI Medical Support system.

1) Navigate to the backend folder and create a virtual environment:

```bash
cd medical_chatbot_backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2) Configure environment variables:

```bash
cp .env.example .env
# Edit .env if needed
# Ensure CORS_ALLOW_ORIGINS includes your frontend origin(s).
# For Kavia cloud preview, include:
# CORS_ALLOW_ORIGINS=http://localhost:3000,https://vscode-internal-30348-beta.beta01.cloud.kavia.ai:4000
```

3) Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) Update the React frontend `.env`:

```
REACT_APP_API_BASE_URL=http://localhost:8000
```

5) Use the app:

- Frontend: http://localhost:3000
- Backend OpenAPI docs: http://localhost:8000/docs

Endpoint summary for the frontend:
- GET `/api/chat/history`
- GET `/api/chat/{session_id}`
- POST `/api/chat`
