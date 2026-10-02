# T-Rep AI — Agent Assist

Real-time AI copilot for T-Mobile care agents. Listens to live conversations via Deepgram, surfaces customer context, explains bill deltas, detects intent, and suggests next-best actions. This repository contains the standalone prototype and architectural codebase for the T-Rep AI retail voice assistant, originally developed as an experiential project for a collaborative hackathon event. It serves as a portfolio demonstration of the interface design, agent logic, and structural framework created during the event. All configurations strictly utilize mock data environments; this code does not connect to, interact with, or contain live company infrastructure, production tools, or sensitive access credentials.

## Stack
- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + Python
- **Speech**: Deepgram Nova-2
- **LLM**: Anthropic Claude (claude-haiku-4-5-20251001)
- **Realtime**: WebSockets

## Quick Start

```bash
# 1. Copy env and fill in keys
cp .env.example .env

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Structure
```
frontend/   React UI (CustomerLookup, CustomerBrief, BillExplorer, ConversationListener, PAHPanel, ExecutionScreen)
backend/    FastAPI routes, LLM service, execution streaming, mock data
```

## Team Roles

| Person | Role | Owns |
|---|---|---|
| P1 | AI/LLM Lead | `agents/`, `prompts/`, `services/llm_service.py`, `services/deepgram_service.py`, brief + bill-delta + intent + PAH routes |
| P2 | Data & Mock Systems Lead | `mock/*.json`, `schemas/customer.py`, `routes/customer.py`, `main.py`, bill calculation utilities |
| P3 | Execution Agent Lead | `services/execution_service.py`, `websocket/execution_ws.py`, `routes/execute.py`, step sequencing + retry logic |
| P4 | Frontend Lead | Design system, `lookup/`, `brief/`, `listener/`, `shared/`, `hooks/useDeepgram.js`, `services/api.js` |
| P5 | Frontend + Demo Lead | `execute/` components, `hooks/useWebSocket.js`, pitch deck, demo script |

**Dependency order:** P2 publishes the data schema first — everyone else builds against it.
