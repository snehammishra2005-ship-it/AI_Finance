# Docker Implementation — Verification

_AI in Finance · `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `requirements.txt`, `.env`_

## 1. Overview

The application runs from one image with two core services (plus an optional
HTTPS proxy) orchestrated by Docker Compose:

| Service | Command | Host port | Role |
|---|---|---|---|
| `backend` | `uvicorn backend.main:app --host 0.0.0.0 --port 8000` | **none (internal only)** | FastAPI: chat, RAG, files, metrics |
| `frontend` | `streamlit run ui/app.py --server.port 8501` | `127.0.0.1:8501` (loopback) | Streamlit UI |
| `caddy` _(production profile)_ | `caddy` (official image) | `80`, `443` | Reverse proxy + automatic HTTPS |

The backend and frontend are built from the same `Dockerfile`
(`python:3.11-slim`) and talk over a private bridge network; the frontend waits
for the backend to be **healthy** before it starts.

**Network posture (P0 #4):** the backend publishes **no host port** — it's
reachable only on the internal network, so there's no open, unauthenticated API
door. The frontend binds to the host's loopback only. In the `production`
profile, **Caddy is the single public entry point** (80/443): it terminates TLS
and forwards to the frontend internally, obtaining a Let's Encrypt certificate
automatically for a real `DOMAIN` (or an internal-CA cert for `localhost`).

## 2. Key implementation decisions

| Concern | Decision |
|---|---|
| GPU-less image size | Install the **CPU-only torch** build (`--extra-index-url https://download.pytorch.org/whl/cpu`) — ~200 MB instead of the ~2.5 GB CUDA wheel |
| Flaky/slow ML wheels | `pip --timeout 120 --retries 10`, plus a BuildKit **pip cache mount** so a retry doesn't re-download gigabytes |
| OCR support | `apt-get install tesseract-ocr` — the binary `pytesseract` shells out to for scanned-PDF and image OCR |
| Embedding model reuse | Named volume `hf-cache:/root/.cache/huggingface` so the sentence-transformers model downloads once, not every rebuild |
| Health, no curl | Healthchecks use `python -c "urllib.request.urlopen(...)"` (curl isn't in the slim base) |
| Ordered startup | `frontend depends_on backend: condition: service_healthy` — the UI never opens onto a "backend didn't start" error |
| Slow first boot | Backend healthcheck `start_period: 180s` (torch import + model download) |
| Secrets / config | `env_file: .env`; the frontend gets `BACKEND_HOST=backend` / `BACKEND_API_URL=http://backend:8000` so it targets the backend service, not localhost |
| Live code | The project is bind-mounted (`.:/app`), so code edits are picked up on restart without a rebuild (dependencies still need a rebuild) |

## 3. How to run

**Local development** (plain HTTP, backend private):

```bash
docker compose up --build -d
```

- UI: http://localhost:8501 — the backend has **no published port** (internal only).
- Rebuild after changing `requirements.txt`; restart (`docker compose restart backend`) after code-only changes.
- On a name/port conflict: `docker compose down --remove-orphans` first.

**Production** (HTTPS via Caddy, single public entry point):

```bash
DOMAIN=app.example.com docker compose --profile production up -d --build
```

- Caddy publishes 80/443 and obtains a Let's Encrypt cert for `DOMAIN`
  automatically; nothing else is exposed publicly. See [`Caddyfile`](./Caddyfile).

## 4. Verification performed

Rebuilt the image (`docker compose up --build -d`) and confirmed the following
**inside the running containers**.

### 4.1 Health & environment
- ✅ Both containers reach **healthy**; `GET /` on the backend returns HTTP 200.
- ✅ Required keys present in the container env (`GROQ_API_KEY`, `TAVILY_API_KEY`, and the added provider keys).

### 4.2 System + Python dependencies (in the backend container)
| Check | Result |
|---|---|
| `tesseract --version` | ✅ **5.5.0** (OCR engine present) |
| `import xlrd` | ✅ 2.0.2 (legacy `.xls` support) |
| `import PIL` (Pillow) | ✅ 12.x (image decoding) |
| Latest code mounted (`IMAGE_EXTS`) | ✅ present (8 image types) |

### 4.3 OCR end-to-end (the path that fails on a bare local host)
- ✅ **Image OCR smoke test:** a generated invoice image, pushed through the same
  `extract_text` dispatch a real upload uses, was read correctly by Tesseract
  inside the container.
- ✅ **Full pipeline on a realistic bank-statement image** via `POST /files`:
  OCR extracted the statement (opening/closing balances, transactions, totals)
  and it was **RAG-indexed** (`rag_indexed: true`).
- ✅ **RAG Q&A** (`POST /rag/ask`): returned the correct **closing balance
  ($4,935.47)** and account holder, with a citation to the source file.
- ✅ **Metric extraction** (`POST /metrics`): returned structured rows
  (opening/closing balance, total debits, interest earned) with the currency
  detected — every figure matching the source image.

### 4.4 Build issues found and fixed (earlier iterations)
| Problem | Fix |
|---|---|
| `ModuleNotFoundError: lightrag` in container | Added `lightrag-hku`, `sentence-transformers` to `requirements.txt` (were venv-only) |
| Build stalled downloading the ~2.5 GB CUDA torch wheel | CPU-only torch index + `--timeout/--retries` + pip cache mount |
| `docker compose up` failed on a stale container name | `docker compose down --remove-orphans` |
| `.xls` / image OCR missing after a prior build | Added `xlrd`, `Pillow`; rebuilt (deps are baked at build time) |

## 5. Verification checklist

| Item | Status |
|---|---|
| Image builds successfully (CPU torch) | ✅ |
| Backend + frontend containers healthy | ✅ |
| Frontend waits for backend (`service_healthy`) | ✅ |
| Backend `/` returns 200 | ✅ |
| Tesseract OCR binary present and working | ✅ |
| `.xls` (xlrd) and image (Pillow) deps present | ✅ |
| Image upload → OCR → RAG index → cited answer | ✅ |
| Metric extraction over OCR'd text | ✅ |
| `.env` keys reach the container | ✅ |
| HF cache volume persists the embedding model | ✅ |

## 6. Notes & caveats

- **Deps are baked at build time**, so any `requirements.txt` change (e.g. adding
  `xlrd`/`Pillow`) needs a **rebuild** (`--build`), not just a restart.
- **Code is bind-mounted**, so code-only edits are picked up on a backend
  restart; the embedding-model change (to `bge-small-en-v1.5`) means existing
  `rag_storage/sessions` should be cleared once and the backend restarted so
  sessions re-index under the new model.
- The compose comment still references the old embedding model name; the active
  model is `BAAI/bge-small-en-v1.5` (same 384-d, so the cache volume still
  applies).
- `.env` is git-ignored and not baked into the image — it's mounted at runtime
  via `env_file`, so secrets never live in the image layers.

## 7. Conclusion

The Docker implementation is **fully functional and verified end-to-end**: the
image builds without a GPU, both services come up healthy in the right order,
and the OCR-dependent paths (image upload, scanned-PDF fallback) — which don't
work on a bare local host without Tesseract — work correctly inside the
container, all the way through RAG indexing, cited Q&A, and metric extraction.
