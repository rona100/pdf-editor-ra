---
paths:
  - "Dockerfile"
  - "docker-compose.yml"
  - ".github/workflows/**"
---

# Docker and CI

- The image installs `libreoffice-writer` and `fonts-dejavu`. Without them, DOCX→PDF fails with a clear error. CI installs them too, otherwise the DOCX→PDF tests skip instead of running.
- Copy `src/` **before** `uv pip install`, because the editable install needs the sources present.
- Copy `README.md` alongside `pyproject.toml`, because hatchling requires it.
- Use an editable install (`-e`) so `__file__`-relative path resolution works at runtime.
- The frontend stage uses `npm install`. `npm ci` would also work now that `package-lock.json` is committed.
- CI runs `uv run --no-sync pytest`. A bare `uv run` re-syncs against `uv.lock` and can half-downgrade the environment.
