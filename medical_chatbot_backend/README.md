# CrewAI Medical Support - FastAPI Backend

A modular FastAPI backend for a demo medical support chatbot with two agents:
- PatientAgent: interactive symptom collection and note structuring (heuristic).
- MedicalAgent: mock RAG over simple vectorized guidelines to produce general recommendations.
  - Strong disclaimer: "Recommendations are not medical advice"

This backend integrates with the provided React frontend via REST.

## Features

- REST API:
  - GET `/api/chat/history` -> list sessions
  - GET `/api/chat/{session_id}` -> session details with messages and recommendations
  - POST `/api/chat` -> `{ session_id?: string|null, message: string }` to send a message
- In-memory chat session store for demo/testing
- Simple vector store and mock embeddings for guideline retrieval
- CORS configured for `http://localhost:3000`
- Environment configuration via `.env`

## Quickstart

1) Create a virtual environment and install dependencies:

```bash
cd medical_chatbot_backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2) Create `.env`:

```bash
cp .env.example .env
# Optionally edit .env
```

3) Run the server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for API docs.

4) Frontend

Ensure the React app has `REACT_APP_API_BASE_URL=http://localhost:8000` in its `.env`.

## Environment Variables

See `.env.example`:
- `PROJECT_NAME` (default: medical_chatbot_backend)
- `CORS_ALLOW_ORIGINS` (default: http://localhost:3000)
- `EMBEDDING_MODEL` (demo default: mock-embedder)
- `VECTOR_DIM` (default: 384)

## Notes

- This project is for demonstration and educational purposes only.
- No data is persisted across server restarts.
- The RAG component is a mock: deterministic pseudo-embeddings + in-memory vector index.

## Container name

As requested, container name: `medical_chatbot_backend`.
