---
title: AI Interview Evaluation Backend
emoji: 🎙️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# AI Interview Evaluation Backend

Production backend API for the AI Interview Evaluation System.
Built with FastAPI, Faster-Whisper (speech recognition), and Microsoft SQL Server / Azure SQL.

## Endpoints
- `GET /health` - Service health diagnostic
- `POST /api/auth/login` - User & Admin Authentication
- `POST /interview/upload` - Audio transcription & automated answer scoring
- `GET /interview/{id}/report` - On-demand in-memory PDF evaluation report generation
