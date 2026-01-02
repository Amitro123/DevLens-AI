# DevLens AI Backend

FastAPI-based backend for DevLens AI with dynamic prompt registry system.

## Features

- 🎯 **Dynamic Prompt Registry** - YAML-based AI persona configuration
- 🤖 **Google Gemini Integration** - Multimodal AI for video analysis
- 📹 **Video Processing** - Frame extraction with OpenCV
- 🔄 **Multiple Documentation Modes**:
  - Bug Report Analysis
  - Feature Specification (PRD)
  - General Technical Documentation

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run the Server
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### `POST /api/v1/upload`
Upload a video and generate documentation.

**Parameters:**
- `file` - Video file (mp4, mov, avi, webm)
- `project_name` - Project name (optional)
- `language` - Language code (en/he)
- `mode` - Documentation mode (bug_report, feature_spec, general_doc)

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "result": "# Generated Documentation\n..."
}
```
{
  "task_id": "uuid",
  "status": "completed",
  "result": "# Generated Documentation\n..."
}
```

### `POST /api/v1/upload/drive`
Import a video from Google Drive and generate documentation.

**Body:**
```json
{
  "url": "https://drive.google.com/file/d/...",
  "session_id": "uuid"
}
```

### `GET /api/v1/modes`
List available documentation modes.

**Response:**
```json
{
  "modes": [
    {
      "mode": "bug_report",
      "name": "Bug Report Analyzer",
      "description": "Analyzes videos to identify bugs..."
    }
  ]
}
```

### `GET /api/v1/status/{task_id}`
Get task processing status.

### `GET /api/v1/result/{task_id}`
Get generated documentation for a completed task.

## Prompt Registry

Prompts are defined in `prompts/*.yaml` files. Each prompt includes:

```yaml
name: "Display Name"
description: "What this mode does"
system_instruction: |
  Detailed AI instructions...
output_format: "markdown"
guidelines:
  - Guideline 1
  - Guideline 2
```

### Adding New Modes

1. Create a new YAML file in `prompts/`
2. Define the prompt configuration
3. Restart the server
4. The new mode will be automatically available

## Testing

Run the MVP test suite:
```bash
python scripts/test_mvp.py
```

Run the End-to-End (E2E) Test Suite (recommended):
```bash
pytest tests/test_e2e_flow.py
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   └── config.py        # Configuration
│   ├── services/
│   │   ├── prompt_loader.py # Dynamic prompt loading
│   │   ├── video_processor.py
│   │   └── ai_generator.py
│   └── api/
│       └── routes.py        # API endpoints
├── prompts/                 # YAML prompt configurations
│   ├── bug_report.yaml
│   ├── feature_spec.yaml
│   └── general_doc.yaml
└── requirements.txt
```
