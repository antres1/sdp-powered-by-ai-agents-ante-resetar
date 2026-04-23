# 7. Deployment View

See [`diagrams/deployment.svg`](diagrams/deployment.svg).

## 7.1 Infrastructure Overview

The system runs as a single Docker container on the developer's local machine.
There are no managed cloud services.

| Layer | Technology | Notes |
|-------|-----------|-------|
| Client | Browser | Static files served from the host (e.g. `python -m http.server`) |
| API | WebSocket server (inside the container) | Exposed via `docker run -p 8000:8000` |
| Auth | PyJWT with a pre-shared signing key | Key injected via env var `JWT_SECRET` |
| Compute | Python 3.12 process in one container | Handles all actions via internal routing |
| Storage | SQLite database file | Persisted to `/data/tcg.db` on a Docker volume |

## 7.2 Infrastructure as Code

All infrastructure lives in the `Dockerfile`:

```
Dockerfile
├── FROM python:3.12-slim
├── WORKDIR /app
├── COPY requirements.txt . && pip install
├── COPY src/ src/
├── COPY tests/ tests/
├── EXPOSE 8000
└── CMD ["python", "-m", "src.main"]
```

An optional `docker-compose.yml` wires the host port and the volume mount:

```yaml
services:
  tcg:
    build: .
    ports: ["8000:8000"]
    volumes: ["tcg-data:/data"]
volumes:
  tcg-data:
```

## 7.3 Deployment Pipeline

```
git push → CI (GitHub Actions)
  → docker build -t tcg-tests .
  → docker run --rm tcg-tests pytest
```

Locally, the same two commands build and test the image. No cloud deployment
step exists for the kata.
