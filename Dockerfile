# Stage 1: Build React
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.13-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv pip install --system -e ".[web]"
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
EXPOSE 8000
CMD ["python", "-m", "pdf_editor", "serve"]
