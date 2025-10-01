# CrewAI Medical Support - React Frontend (Ocean Professional)

A modern, production-ready React UI for interacting with the CrewAI-based medical support chatbot.  
Implements a centered chat panel, side cards for history and recommendations, and a branded header with responsive design.

## Features

- Ocean Professional theme (blue and amber accents) with subtle shadows, rounded corners, gradients, and smooth transitions
- Centered chat panel for user and agent messages
- Side panel with conversation history and dynamic recommendations
- Responsive layout for desktop and mobile
- REST API integration with FastAPI backend:
  - GET `/api/chat/history` — list of sessions
  - GET `/api/chat/{session_id}` — conversation details
  - POST `/api/chat` — send a message (accepts `{ session_id?, message }`)
- Clear error handling and optimistic UI for message sending
- No heavy UI frameworks; pure React + CSS

## Getting Started

1) Install dependencies

```bash
npm install
```

2) Set environment variables

Copy `.env.example` to `.env` and set the backend URL.

```bash
cp .env.example .env
# edit .env and set REACT_APP_API_BASE_URL=http://localhost:8000
```

3) Run the development server

```bash
npm start
```

Open http://localhost:3000 to view the app.

## Environment Variables

- `REACT_APP_API_BASE_URL` (required): Base URL of your FastAPI backend (e.g., `http://localhost:8000`)
- `REACT_APP_SITE_URL` (optional): Site URL for redirect purposes if needed by the backend

## Expected Backend Endpoints

Adjust paths in `src/App.js` if needed:
- `GET /api/chat/history` => `[{ id, title?, created_at?, updated_at? }]`
- `GET /api/chat/{session_id}` => `{ id, messages: [{ role, content, timestamp? }], recommendations?: [string] }`
- `POST /api/chat` with JSON `{ session_id?: string|null, message: string }`  
  Returns `{ id, messages, recommendations? }`

## Production Build

```bash
npm run build
```

This will create an optimized production build in the `build` folder.

## Notes

- The UI includes a persistent disclaimer emphasizing informational use only, not medical advice.
- The design avoids third-party UI kits, maintaining a lightweight footprint.
