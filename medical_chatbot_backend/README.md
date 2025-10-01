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

Troubleshooting: ModuleNotFoundError: No module named 'fastapi'
- Ensure dependencies are installed from requirements.txt (inside an activated venv is recommended):
  ```bash
  python -m pip install --upgrade pip
  pip install --upgrade --force-reinstall -r requirements.txt
  ```
- If you cannot use a virtual environment in your environment, pip will default to user installs; still ensure the above completes successfully before starting uvicorn.

Note on dependencies:
- This backend pins Pydantic and pydantic-core versions to satisfy shelly-ai==0.1.4 requirements (pydantic==2.10.6, pydantic-core==2.27.2) and uses a compatible FastAPI version.
- If you previously installed dependencies, please reinstall to apply the updated pins:
  ```bash
  pip install --upgrade --force-reinstall -r requirements.txt
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
  - Comma-separated list of allowed origins for CORS.
  - Include your frontend origin(s). For Kavia cloud preview, add:
    `https://vscode-internal-30348-beta.beta01.cloud.kavia.ai:4000`
  - Example:
    ```
    CORS_ALLOW_ORIGINS=http://localhost:3000,https://vscode-internal-30348-beta.beta01.cloud.kavia.ai:4000
    ```
- `EMBEDDING_MODEL` (demo default: mock-embedder)
- `VECTOR_DIM` (default: 384)

## Notes

- This project is for demonstration and educational purposes only.
- No data is persisted across server restarts.
- The RAG component is a mock: deterministic pseudo-embeddings + in-memory vector index.
- PatientAgent and MedicalAgent now use session-scoped memory to avoid repeating questions and to gate medicine suggestions until triage is complete.

## Tests

Run unit tests (if pytest available):

```bash
cd medical_chatbot_backend
pytest -q
```

Tests validate:
- PatientAgent does not repeat questions across turns and marks triage completion.
- MedicalAgent withholds medicine suggestions until triage is complete, then includes them with a disclaimer.

## Container name

As requested, container name: `medical_chatbot_backend`.
