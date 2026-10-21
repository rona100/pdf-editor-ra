---
paths:
  - "src/pdf_editor/api/**"
  - "src/pdf_editor/_serve.py"
  - "src/pdf_editor/__main__.py"
  - "tests/test_api.py"
---

# Web API

- Routes wrap `pdf_operations` functions with file I/O and error translation. Never change `pdf_operations` to get a different API behavior.
- Each request works in a temporary directory. Cleanup runs through `BackgroundTasks` *after* the `FileResponse` has been sent, because deleting it earlier breaks streaming.
- CORS allows only `localhost:5173` (the Vite dev server). Production serves the React build from the same origin.
- `app.py` resolves `frontend/dist` through the `FRONTEND_DIST` env var (set in docker-compose). Without it, it falls back to a `__file__`-relative path, which works for local dev with an editable install.
- `__main__.py` checks for a `serve` argument before routing to the CLI. Keep the two modes uncoupled.
