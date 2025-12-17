# 🛣️ DevLens AI Roadmap

This document outlines the planned features and development priorities for DevLens AI.

## ✅ Q4 2025: MVP Stabilization & Core Memory

The primary goal for this quarter is to solidify the MVP, ensure it's stable end-to-end, and integrate the core memory infrastructure.

- [x] **MVP: Synchronous video processing**
- [x] **Dynamic prompt registry system**
- [x] **React frontend with mode selection**
- [x] **Calendar integration with draft sessions**
- [x] **Audio-first smart sampling with Gemini Flash**
- [x] **Google Drive Integration (Import via URL)**
- [ ] **Manual End-to-End Testing & Bug Fixes**
    - [ ] Verify the entire flow: Video Upload → Markdown Generation
    - [ ] Fix blocking I/O issues with `run_in_threadpool`
    - [ ] Resolve documentation/branding inconsistencies
- [x] **Acontext Integration (Core Memory Layer)** *(Flight Recorder)*
    - [x] Integrate Acontext via Docker Compose
    - [x] Create `observability.py` with `AcontextClient` and `@trace_pipeline` decorator
    - [x] Instrument pipeline: `extract_audio`, `extract_frames`, `analyze_audio_relevance`, `generate_documentation`
    - [x] Store final documentation and code blocks as artifacts
- [ ] **MCP Server Integration (Agent Connectivity)**
    - [ ] Implement `fastapi-mcp` to expose memory endpoints
    - [ ] Define tools for searching memory and retrieving session context
    - [ ] Document how to connect Antigravity/Cursor to the MCP server

## 🚀 Q1 2026: "Smart Context" & Enhanced AI

Focus on making the agent smarter by improving its understanding of context and providing richer data.

- [ ] **Advanced OCR for Code Extraction**
    - [ ] Integrate PaddleOCR or a similar dedicated OCR library
    - [ ] Implement a two-stage process: OCR for raw text, LLM for cleanup
- [ ] **Speaker Diarization**
    - [ ] Integrate `pyannote.audio` to identify different speakers
    - [ ] Tag the generated documentation with `Speaker A`, `Speaker B`, etc.
- [ ] **"Deep Linking" in UI**
    - [ ] Connect Markdown sections to video timestamps
    - [ ] Allow users to click on a summary point and jump to the relevant video segment
- [ ] **Real Calendar API Integration**
    - [ ] Move from mock data to real Google Calendar / Outlook integration
- [ ] **Real Export API Integration**
    - [ ] Implement real Notion & Jira API calls (move from mock)

## 🧠 Q2 2026: "Organizational Brain" & Production Readiness

Transition from a smart tool to a self-improving "organizational brain" ready for enterprise use.

- [ ] **Advanced RAG on Organizational Docs**
    - [ ] Implement entity linking (components, services, projects)
    - [ ] Connect to the company's codebase/documentation for deeper context
- [ ] **Self-Improving Memory Loop**
    - [ ] Use Acontext's "Experience Agent" to learn from past sessions
    - [ ] The agent should get better at summarizing bugs or features for specific projects over time
- [ ] **Privacy-First Local Mode**
    - [ ] Support for local models via Ollama (e.g., Llama 3.2 Vision)
    - [ ] Allow running the entire pipeline on-premise for sensitive organizations
- [ ] **Full Async Processing**
    - [ ] Migrate from `run_in_threadpool` to a robust Celery + Redis background worker queue
    - [ ] Implement WebSockets or polling for real-time frontend progress updates

## 🌐 Future Vision: Multi-Language & Beyond

- [ ] **Multi-language Support (Hebrew/English)**
- [ ] **Alternative AI Writer Engines (Claude 3.5 Sonnet)**
- [ ] **Expanded Integrations (Slack, Confluence, etc.)**