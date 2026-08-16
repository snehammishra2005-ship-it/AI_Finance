# Production Readiness — Missing Features

_A plain-language guide to what the **AI in Finance** project still needs before it can
safely serve real users. Each item says **what it is**, **why it matters**, and **what to
do** — written to be understandable without deep DevOps knowledge._

---

## First, the good news — what's already done

The app is **functionally solid**. These things were once gaps and are now handled, so
they are **not** on the to-do list below:

- ✅ **Per-session RAG isolation** — one user's uploaded documents never leak into another
  user's answers.
- ✅ **Provider fallback routing** — if the chosen LLM fails, it automatically retries a
  different provider, so one outage doesn't break chat.
- ✅ **CORS locked down** — the backend only accepts requests from the app's own origins,
  not "anyone on the internet."
- ✅ **Token streaming for chat** — plain chat answers appear word-by-word.
- ✅ **Safe file uploads** — real file type is detected from content (not just the name),
  and a 25 MB size cap prevents memory-exhaustion.
- ✅ **Honest error handling** — a real provider failure returns a proper error (HTTP 502),
  never a fake "answer."
- ✅ **Offline test suite** — 55 unit tests for the deterministic logic.

So the work that remains is almost entirely **operational, security, and scale** — the gap
between "works on my machine" and "safe for real users."

The items below are grouped by priority: **P0** (do first / blockers) down to **P3**
(nice-to-have polish).

---

## 🔴 P0 — Blockers (must do before ANY shared deployment)

These are the "someone could get hurt or you could lose money" items.

### 1. Authentication (login)
- **What it is:** A way to prove who a user is before they can use the app.
- **Current state:** There is **none**. No login, no accounts, no API keys. The backend
  (`:8000`) is wide open.
- **Why it matters:** Anyone who can reach the app can use it freely — **spending your paid
  API credits** (Groq, Tavily) and uploading documents. There is nothing stopping abuse.
- **What to do:** Add an authentication layer. Even a single shared password gate is a big
  improvement; ideally, proper per-user login (e.g. JWT / session tokens).

### 2. Per-user data isolation for chat history
- **What it is:** Each user should only see their own saved conversations.
- **Current state:** RAG documents are isolated per session ✅, but **chat history is
  global** — the code reads *every* saved chat file from one shared folder, so **every
  browser sees everyone's chats**.
- **Why it matters:** It's a real privacy leak the moment more than one person uses the app.
- **What to do:** Scope saved history to the logged-in user (needs #1 first).

### 3. Secrets management
- **What it is:** How API keys and passwords are stored.
- **Current state:** Kept in a plain `.env` file.
- **Why it matters:** A `.env` file is fine for local development, but risky in production —
  secrets can leak through backups, logs, or a compromised server.
- **What to do:** Use a proper secrets store (e.g. AWS Secrets Manager, HashiCorp Vault, or
  your cloud provider's equivalent). Never bake secrets into the image or commit them.

### 4. HTTPS / TLS and network posture
- **What it is:** Encrypting traffic between the browser and the server, and not exposing
  internal services.
- **Current state:** Plain HTTP. In Docker, the backend port `:8000` is published to the
  host alongside the frontend.
- **Why it matters:** Without HTTPS, passwords and documents travel unencrypted. Exposing
  the backend directly gives attackers a second, unauthenticated door.
- **What to do:** Put a reverse proxy (nginx / Traefik / Caddy) in front with HTTPS. Expose
  **only** the frontend publicly; keep the backend on an internal network.

### 5. Rate limiting / abuse control
- **What it is:** Limits on how many requests or uploads a single user can make.
- **Current state:** None on any endpoint.
- **Why it matters:** One user (or a bot) can hammer the app, drain your API budget, or fill
  the disk with uploads.
- **What to do:** Add per-user / per-IP rate limits and upload throttling.

---

## 🟠 P1 — Scale & durability (needed for real, growing usage)

These stop the app from falling over or losing data as usage grows.

### 6. Real persistence (database + storage)
- **What it is:** Where data actually lives.
- **Current state:** Everything is **files on disk** — chat history as JSON
  (`data/history`), uploads (`data/uploads`), RAG stores (`rag_storage/sessions`), and
  analysis CSVs.
- **Why it matters:** Files on one machine don't scale, are hard to back up, and break the
  moment you run more than one copy of the app.
- **What to do:** Move to a database (e.g. **Postgres**) for history/metadata, **object
  storage** (e.g. S3) for uploaded files, and a **managed vector database** for RAG at scale.

### 7. Multi-instance / horizontal scaling
- **What it is:** Running several copies of the app behind a load balancer to handle more
  users.
- **Current state:** Single process; file storage and the in-memory session cache assume one
  machine.
- **Why it matters:** You can't just "add another server" today — the copies wouldn't share
  data.
- **What to do:** Externalize all state (see #6) so any replica can serve any user, then run
  multiple replicas behind a load balancer.

### 8. Durable sessions
- **What it is:** Keeping a user's session (and their uploaded docs) alive across page
  refreshes and restarts.
- **Current state:** The session ID lives only in the browser's Streamlit memory — a hard
  refresh resets it, and there's no way to resume earlier RAG documents.
- **Why it matters:** Users lose their context unexpectedly.
- **What to do:** Persist sessions so they survive refresh and server restarts.

### 9. Cost controls
- **What it is:** Tracking and limiting how much each user costs in API calls.
- **Current state:** No metering. The app leans on free tiers, and 2–3 providers are already
  out of credit.
- **Why it matters:** Without limits, costs are unpredictable and a single heavy user can be
  expensive.
- **What to do:** Add token/cost metering and per-user quotas; move to paid provider tiers
  for reliability.

### 10. Encryption at rest
- **What it is:** Encrypting stored data so it's unreadable if the disk is stolen or leaked.
- **Current state:** Uploads, history, CSVs, and RAG stores are all plaintext on disk.
- **Why it matters:** Financial documents are sensitive; plaintext at rest is a data-breach
  risk.
- **What to do:** Encrypt sensitive stores, or use encrypted managed storage.

### 11. Data retention & privacy rights
- **What it is:** Rules for how long data is kept and letting users delete/export their data.
- **Current state:** Uploaded files stay in `data/uploads/` forever; there's no delete or
  export.
- **Why it matters:** Indefinite retention of financial data is a legal/compliance risk
  (e.g. GDPR).
- **What to do:** Add a retention policy plus user data export and deletion.

---

## 🟡 P2 — Reliability & operations (keep it healthy in production)

These are how you *run* the app confidently once it's live.

### 12. Observability (logs, metrics, error tracking)
- **What it is:** Being able to see what the app is doing and when it breaks.
- **Current state:** Basic logging only.
- **Why it matters:** When something fails in production, you need to know fast and be able
  to diagnose it.
- **What to do:** Add structured logs with request IDs, metrics/dashboards, an error tracker
  (e.g. Sentry), and separate `/health` (alive) vs `/ready` (ready to serve) checks.

### 13. CI/CD (automated testing & deployment)
- **What it is:** Automatically running tests on every change and deploying safely.
- **Current state:** No pipeline — the 55 tests aren't run automatically.
- **Why it matters:** Manual testing and deploys are slow and error-prone; bugs slip through.
- **What to do:** Set up GitHub Actions (or similar) to run tests/lint on every pull request
  and automate deployment.

### 14. Integration / end-to-end tests
- **What it is:** Tests that exercise the whole flow, not just small helper functions.
- **Current state:** Only offline unit tests for the deterministic pieces.
- **Why it matters:** The important behaviors — the API endpoints, RAG isolation, the
  fallback router, and (once added) auth — aren't automatically verified.
- **What to do:** Add integration/E2E tests for those flows.

### 15. Backups & disaster recovery
- **What it is:** Copies of your data you can restore after a failure.
- **Current state:** None.
- **Why it matters:** A disk failure today means permanent data loss.
- **What to do:** Automated backups for the database and uploaded files, with a tested
  restore process.

### 16. Prompt-injection hardening
- **What it is:** Protecting the model from malicious instructions hidden inside uploaded
  documents or web results.
- **Current state:** Retrieved document/web text is fed to the model as-is.
- **Why it matters:** A crafted document could try to make the assistant misbehave or leak
  its instructions.
- **What to do:** Add guardrails that treat retrieved content as untrusted data, not
  instructions.

---

## 🟢 P3 — Product polish (not blockers, but improve the experience)

- **Hide/disable broken model options** — providers that are out of credit still appear in
  the dropdown and just error; grey them out.
- **Stream web/RAG answers too** — only plain chat streams today, so research answers feel
  slow.
- **A "documents in this session" panel** — let users see and remove what they've uploaded.
- **Mobile & accessibility** — the layout is desktop-first.
- **Smarter provider routing** — the current fallback is reactive (it retries only *after* a
  failure) rather than tracking each provider's remaining quota.

---

## Summary checklist

| # | Item | Priority |
|---|------|:--:|
| 1 | Authentication (login) | 🔴 P0 |
| 2 | Per-user chat history | 🔴 P0 |
| 3 | Secrets management | 🔴 P0 |
| 4 | HTTPS/TLS + hide backend port | 🔴 P0 |
| 5 | Rate limiting / abuse control | 🔴 P0 |
| 6 | Real database + object/vector storage | 🟠 P1 |
| 7 | Multi-instance / horizontal scaling | 🟠 P1 |
| 8 | Durable sessions | 🟠 P1 |
| 9 | Cost metering + per-user quotas | 🟠 P1 |
| 10 | Encryption at rest | 🟠 P1 |
| 11 | Data retention + export/delete | 🟠 P1 |
| 12 | Observability (logs/metrics/errors) | 🟡 P2 |
| 13 | CI/CD pipeline | 🟡 P2 |
| 14 | Integration / E2E tests | 🟡 P2 |
| 15 | Backups & disaster recovery | 🟡 P2 |
| 16 | Prompt-injection hardening | 🟡 P2 |
| 17 | Product polish (UI, streaming, mobile) | 🟢 P3 |

---

## Suggested order of work

1. **Lock the front door first (P0):** authentication → per-user history → HTTPS + hide the
   backend port → rate limiting → move secrets out of `.env`.
2. **Make data durable and scalable (P1):** swap file storage for a database + object/vector
   store; this also unlocks running multiple copies and doing backups.
3. **Run it with confidence (P2):** add monitoring, CI/CD, more tests, and backups.
4. **Polish the experience (P3):** UI cleanups and streaming everywhere.

**Bottom line:** the product logic is in good shape. The road to production is dominated by
**#1 authentication** and **#2 per-user history**, then replacing **file-based storage with a
real database + object/vector store**. Everything else builds on top of those.
