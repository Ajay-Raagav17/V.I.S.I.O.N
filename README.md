# V.I.S.I.O.N — AI-Powered Educational Accessibility Platform

<div align="center">

**Transforming how deaf and hard-of-hearing students experience classroom learning**

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![AssemblyAI](https://img.shields.io/badge/AssemblyAI-Transcription-blue)](https://www.assemblyai.com/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-AI%20Analysis-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)

</div>

---

## Overview

V.I.S.I.O.N is an AI-powered educational accessibility platform that converts live classroom audio or uploaded recordings into clean transcripts, topic-wise notes, and intelligent summaries — empowering deaf and hard-of-hearing students with real-time access to lecture content.

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Live Captioning** | Stream audio and receive captions with <2s latency |
| **Audio Upload Processing** | Upload recorded lectures for transcription and analysis |
| **AI-Powered Study Notes** | Automatic topic extraction, summaries, and key points |
| **PDF Export** | Download formatted study materials as clean PDFs |
| **Lecture History** | Access, manage, and share past lectures and notes |
| **User Authentication** | Secure JWT-based login and registration |

## Tech Stack

### Frontend
- **React 18** with JavaScript
- **Vite** for fast development and builds
- **Tailwind CSS** + custom design system for styling
- **React Router** for navigation

### Backend
- **Python** with **FastAPI**
- **PostgreSQL** database with **SQLAlchemy** ORM
- **Alembic** for database migrations
- **JWT** authentication

### AI Services
- **AssemblyAI** — Speech-to-text transcription (free tier: 5 hours/month)
- **Google Gemini** — AI-powered content analysis, summarization, and note generation

### Deployment
- **Vercel** serverless functions
- **Vercel Postgres** for database
- **Vercel Blob** for file storage

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.9+
- **PostgreSQL** database
- **AssemblyAI** API key — [Get free key](https://www.assemblyai.com/)
- **Gemini AI** API key — [Get free key](https://makersuite.google.com/app/apikey)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/V.I.S.I.O.N.git
   cd V.I.S.I.O.N
   ```

2. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database URL
   ```

3. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

5. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

### Running Locally

**Start the backend server:**
```bash
python -m uvicorn api.main:app --reload
```

**Start the frontend dev server (in a separate terminal):**
```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`

### Running Tests

**Backend tests:**
```bash
pytest
```

**Frontend tests:**
```bash
cd frontend
npm test
```

## Project Structure

```
V.I.S.I.O.N/
├── api/                    # FastAPI application & route handlers
│   ├── main.py             # App entry point
│   ├── auth/               # Authentication endpoints
│   ├── live/               # Live captioning endpoints
│   ├── upload/             # Audio upload endpoints
│   ├── notes/              # Notes & analysis endpoints
│   └── lectures/           # Lecture history endpoints
├── services/               # Business logic layer
│   ├── auth_service.py     # Authentication logic
│   ├── transcription_service.py  # AssemblyAI integration
│   ├── ai_analysis_service.py    # Gemini AI integration
│   ├── pdf_service.py      # PDF generation
│   └── audio_processing_service.py  # Audio pipeline
├── models/                 # SQLAlchemy database models
│   ├── lecture.py           # Lecture model
│   └── user.py             # User model
├── database/               # Database connection & utilities
├── alembic/                # Database migration scripts
├── tests/                  # Backend test suite
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── auth/       # Login, Register, Forgot Password
│   │   │   ├── dashboard/  # Dashboard layout & home
│   │   │   ├── live/       # Live captioning UI
│   │   │   ├── upload/     # File upload interface
│   │   │   └── notes/      # Notes viewer
│   │   ├── styles/         # CSS styles & design system
│   │   └── services/       # API client services
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
└── README.md
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `ASSEMBLYAI_API_KEY` | AssemblyAI API key for transcription |
| `GEMINI_API_KEY` | Google Gemini API key for AI analysis |
| `JWT_SECRET` | Secret key for JWT token signing |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time (default: 30) |
| `FRONTEND_URL` | Frontend URL for CORS (default: http://localhost:5173) |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size (default: 100) |
| `ALLOWED_AUDIO_FORMATS` | Supported audio formats |

## Screenshots

### Login Page
Clean, modern split-screen design with gradient branding panel.

### Dashboard
Minimalist dashboard with stat cards, feature quick actions, and lecture history.

## License

MIT

---

<div align="center">
  <sub>Built with ❤️ for educational accessibility</sub>
</div>
