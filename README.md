# SafeHome AI — Premium AI-Powered Home Safety Platform

[![Amazon Developer Hackathon](https://img.shields.io/badge/Amazon%20Developer%20Hackathon-Ring%20Track-168653.svg)](https://developer.ring.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20Tailwind-61DAFB.svg)](https://vitejs.dev)
[![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV%204.10-5C3EE8.svg)](https://opencv.org)

**SafeHome AI** is a home safety web application built for the Amazon Developer Hackathon (Ring Track). It provides security video analysis, evidence-grounded AI safety summaries, real-time Ring camera monitoring, and human review workflows.

---

## 🌟 Key Features

1. **Balanced Green-and-White SaaS Dashboard**:
   - Primary Green: `#168653`, Deep Accent: `#116B43`, Soft Green: `#EFF7F1`, White Cards: `#FFFFFF`, Main Text: `#182820`.
   - Real-time KPI summary cards (Total Events, Review Pending, AI Summarized, Connected Devices).
   - Video Player with interactive scrubber, timestamp overlay, and clip inspector.
   - Detected events timeline with video frame thumbnails and priority badges (`Low`, `Medium`, `High`).

2. **Video Upload & Processing Pipeline**:
   - Supports MP4, MOV, AVI, WEBM (up to 200MB, 10 min duration).
   - OpenCV frame sampling and MOG2 background subtraction for motion contour tracking.
   - Background job runner with progress feedback.

3. **Evidence-Grounded AI Summaries**:
   - Generates objective, visually verifiable summaries without fabricating intent or assumptions.
   - Distinct sections: Observed sequence, visual evidence, unknowns/unverified details, review rationale, and suggested next steps.
   - Export reports in Markdown or JSON.

4. **Amazon Vision / Ring Partner Integration**:
   - Adheres to the official **Amazon Vision Partner API** (`https://api.amazonvision.com`) and **JSON:API Specification**.
   - HMAC SHA-256 signature verification for incoming webhooks (`/api/ring/webhook`).
   - Built-in Ring Sandbox Simulator to trigger doorbell rings, person detection, motion events, and package dropoffs without physical hardware.
   - Multi-camera live view monitor supporting WebRTC/WHEP simulation.

5. **Human Review & Notification Center**:
   - Prioritized in-app alerts (Low, Medium, High).
   - Review states: `Pending Review`, `Reviewed`, `Acknowledged`, `Dismissed`.
   - Audit trail of review actions.

6. **Privacy & Data Governance**:
   - Configurable video retention policy (7, 30, 90 days, indefinite).
   - Facial anonymization blur toggle.
   - Local edge processing mode (zero cloud transmission).
   - Storage usage breakdown (uploads, frames, SQLite database).
   - Non-destructive demo reset.

---

## 🏗️ Architecture

```
SafeHome_Ai/
├── backend/
│   ├── app/
│   │   ├── config.py             # Pydantic BaseSettings & env loading
│   │   ├── database.py           # SQLAlchemy SQLite engine & session
│   │   ├── models.py             # Video, Event, AISummary, RingDevice, Notification, Privacy
│   │   ├── schemas.py            # Pydantic v2 schemas
│   │   ├── main.py               # FastAPI app, static mounts, demo seeder
│   │   ├── services/
│   │   │   ├── video_processor.py # OpenCV metadata, sampling, motion contours
│   │   │   ├── ai_analyzer.py     # Gemini Vision, OpenAI Vision, Local Edge CV
│   │   │   ├── ring_service.py    # Amazon Vision Partner API, HMAC webhooks, simulator
│   │   │   └── notification_service.py # In-app notification & review logger
│   │   └── routers/
│   │       ├── dashboard.py       # Live DB-calculated KPI stats
│   │       ├── videos.py          # Upload, stream, frame serving, job status
│   │       ├── events.py          # Timeline filter, search, review patch
│   │       ├── summaries.py       # Summaries retrieval, regenerate, export
│   │       ├── ring.py            # Device discovery, sync, webhook, simulator
│   │       ├── notifications.py   # Alerts list, mark read
│   │       └── settings.py        # Model config, privacy, storage metrics
│   ├── tests/
│   │   └── test_api.py            # Pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/            # Sidebar, Topbar, Player, Timeline, Cards
│   │   ├── pages/                 # 10 core pages
│   │   ├── services/              # Axios API client & TypeScript interfaces
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css              # Custom Tailwind design tokens
│   ├── package.json
│   └── vite.config.ts             # Dev server & API proxy
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env from template
copy .env.example .env

# Run automated tests
python -m pytest tests/test_api.py -v

# Start FastAPI dev server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend starts at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is accessible at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Start Vite dev server
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## ⚙️ AI Vision Model Configuration

SafeHome AI supports three visual analysis modes:

| Provider | Setting | Key Required? | Description |
|---|---|---|---|
| **Local Edge CV (Default)** | `AI_PROVIDER=mock` | **No** | Uses OpenCV MOG2 background subtraction and optical contours. 100% offline and clearly labeled. |
| **Google Gemini Vision** | `AI_PROVIDER=gemini` | Yes (`GEMINI_API_KEY`) | Analyzes keyframes using `gemini-1.5-flash` with strict visual grounding instructions. |
| **OpenAI GPT-4o-mini Vision** | `AI_PROVIDER=openai` | Yes (`OPENAI_API_KEY`) | Multi-frame vision extraction via `gpt-4o-mini`. |

You can toggle providers and enter API keys directly in the **Settings** page within the app.

---

## 🔔 Amazon Vision / Ring Hackathon Integration

- **Partner API URL**: `https://api.amazonvision.com`
- **Specification**: JSON:API Standard
- **Webhooks**: Real-time event notifications (`motion`, `ding`, `person`, `package_delivered`) signed with HMAC SHA-256 (`X-Ring-Signature`).
- **Simulator Mode**: `RING_SIMULATOR_MODE=True` allows full evaluation of event ingestion and alerts without physical camera hardware.
- Use the **Ring Integration** page in the dashboard to trigger simulated events or synchronize discovered devices.
