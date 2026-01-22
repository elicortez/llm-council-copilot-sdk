# CLAUDE.md - Technical Notes for LLM Council

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

**This fork uses the GitHub Copilot SDK** instead of OpenRouter, allowing you to leverage your existing Copilot subscription to access multiple LLMs.

## Architecture

### Backend Structure (`backend/`)

**`config.py`**
- Contains `DEFAULT_COUNCIL_MODELS` (list of Copilot SDK model identifiers)
- Contains `DEFAULT_CHAIRMAN_MODEL` (model that synthesizes final answer)
- Contains `SETTINGS_FILE` path for persisting user preferences
- Backend runs on **port 8001** (NOT 8000 - user had another app on 8000)

**`copilot_client.py`** - Copilot SDK Integration
- Singleton `CopilotClient` managed via FastAPI lifespan
- `start_client()` / `stop_client()`: Lifecycle management
- `get_available_models()`: Returns models from user's Copilot subscription
- `validate_models()`: Checks default models at startup, logs warnings
- `query_model()`: Single async model query using ephemeral sessions
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns structured dict with 'content', 'model', and optional 'error'

**`council.py`** - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all council models
- `stage2_collect_rankings()`:
  - Filters to successful responses only
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text, `parsed_ranking` list, and optional `error`
- `stage3_synthesize_final()`: Chairman synthesizes from successful responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section
- `calculate_aggregate_rankings()`: Computes average rank position across peer evaluations
- All functions accept optional `council_models` and `chairman_model` parameters

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, title, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- **Settings management**: `get_settings()` / `save_settings()` for global config in `data/settings.json`
- Settings include: `council_models` (list) and `chairman_model` (string)

**`main.py`**
- FastAPI app with CORS enabled for localhost:5173 and localhost:3000
- **Lifespan handler**: Starts/stops Copilot client on app startup/shutdown
- `GET /api/models`: Returns available models from Copilot
- `GET /api/settings` / `POST /api/settings`: Manage council configuration
- `POST /api/conversations/{id}/message`: Returns metadata in addition to stages
- Streaming endpoint sends stage progress via SSE

### Frontend Structure (`frontend/src/`)

**`api.js`**
- `fetchModels()`: Get available models from backend
- `getSettings()` / `saveSettings()`: Manage council configuration

**`App.jsx`**
- Main orchestration: manages conversations list and current conversation
- Handles message sending and metadata storage
- Opens Settings modal via `isSettingsOpen` state

**`components/Settings.jsx`**
- Modal for configuring council models and chairman
- Multi-select checkboxes for council members
- Single-select dropdown for chairman
- Fetches models dynamically from `/api/models`

**`components/Sidebar.jsx`**
- Settings button in footer opens the Settings modal

**`components/Stage1.jsx`**
- Tab view of individual model responses
- **Warning banners** for failed models
- Filters to show only successful responses in tabs

**`components/Stage2.jsx`**
- Tab view showing RAW evaluation text from each model
- De-anonymization happens CLIENT-SIDE for display
- **Warning banners** for ranking failures
- Shows "Extracted Ranking" below each evaluation

**`components/Stage3.jsx`**
- Final synthesized answer from chairman
- Green-tinted background (#f0fff0) to highlight conclusion

### Error Handling Philosophy
- Continue with successful responses if some models fail (graceful degradation)
- Never fail the entire request due to single model failure
- Log errors but don't expose to user unless all models fail

### UI/UX Transparency
- All raw outputs are inspectable via tabs
- Parsed rankings shown below raw text for validation
- Users can verify system's interpretation of model outputs
- This builds trust and allows debugging of edge cases

## Important Implementation Details

### Relative Imports
All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration
- Backend: 8001 (changed from 8000 to avoid conflict)
- Frontend: 5173 (Vite default)
- Update both `backend/main.py` and `frontend/src/api.js` if changing

### Markdown Rendering
All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing. This class is defined globally in `index.css`.

### Model Configuration
Models are hardcoded in `backend/config.py`. Chairman can be same or different from council members. The current default is Gemini as chairman per user preference.

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root, not from backend directory
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Ranking Parse Failures**: If models don't follow format, fallback regex extracts any "Response X" patterns in order
4. **Missing Metadata**: Metadata is ephemeral (not persisted), only available in API responses
5. **Copilot CLI Auth**: Must run `copilot auth login` before starting the backend

## Future Enhancement Ideas

- Streaming token deltas within each stage (currently stages stream, not tokens)
- Export conversations to markdown/PDF
- Model performance analytics over time
- Custom ranking criteria (not just accuracy/insight)
- Support for reasoning models with special handling
- Session reuse for faster response times

## Testing Notes

Ensure the Copilot CLI is authenticated before running:
```bash
copilot auth status
```

If not authenticated, run:
```bash
copilot auth login
```

## Data Flow Summary

```
User Query
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.
