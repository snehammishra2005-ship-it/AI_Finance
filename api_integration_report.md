# API Integration — Technical Report

**Subject:** How the AI in Finance backend integrates external APIs — the
multi-provider LLM router, the RAG completion adapter, and the web-search
integration.

---

## 1. Overview

The project talks to **five external APIs** across three independent
integration paths:

| Path | Purpose | APIs used |
|------|---------|-----------|
| **LLM router** | Chat + document analysis answers | OpenRouter, Google Gemini, Groq, Anthropic |
| **RAG adapter** | Entity extraction + querying over uploaded docs | Groq (async) |
| **Web search** | "Search the web" sources in chat | Tavily |

All API keys are read from environment variables (loaded from `.env` via
`python-dotenv` at backend startup). No key is ever hard-coded.

---

## 2. The LLM router (primary API integration)

The core integration is a **provider-router pattern** that lets the app swap
between LLM vendors behind one uniform interface.

### 2.1 Provider abstraction — `backend/services/api_providers.py`

A base class defines the contract every provider implements:

```python
class BaseLLMProvider:
    def __init__(self, model_id: str): ...
    def generate_response(self, system_prompt: str, user_message: str) -> str
```

Four concrete providers subclass it. Each **imports its SDK lazily inside
`__init__`** (not at module top level), so a missing SDK or key only breaks
that one provider — the rest keep working.

| Provider class | SDK | Auth | Notable handling |
|----------------|-----|------|------------------|
| `OpenRouterProvider` | `openai` | `OPENROUTER_API_KEY` | Uses the OpenAI SDK with `base_url="https://openrouter.ai/api/v1"` — OpenRouter is OpenAI-compatible |
| `GeminiProvider` | `google-generativeai` | `GEMINI_API_KEY` | Gemini has no "system" role, so system + user are **concatenated** into one prompt |
| `GroqProvider` | `groq` | `GROQ_API_KEY` | Standard OpenAI-style `messages` array |
| `AnthropicProvider` | `anthropic` | `ANTHROPIC_API_KEY` | `system` passed as a **top-level parameter**, not a message |

Common settings across providers: `temperature=0.7`, `max_tokens=512`. Each
provider wraps its API call in try/except and, on failure, **returns a
readable error string** (e.g. `"Groq Error: ..."`) rather than raising — so
one provider failing never crashes the request.

### 2.2 Routing engine — `backend/services/llm_service.py`

`LLMEngine` (a singleton) is the traffic controller:

- **`load_model(model_name)`** — sets the active model. Looks the name up in
  `SLM_LIST`, falls back to the default (first entry) if not found.
- **`_get_provider_instance(config)`** — maps `provider` type →
  provider class, and **caches instances** by `provider_model_id` so heavy
  SDK clients aren't re-created on every call.
- **`generate_response(message, persona)`** — pulls the persona instructions
  (`utils/persona_manager`), builds the system prompt, and dispatches to the
  selected provider.

If a provider can't be initialized (missing key, etc.), the engine returns a
graceful `"Error: Could not initialize provider… Please check API keys."`

### 2.3 Configuration — `config/slm_config.py`

`SLM_LIST` is the single source of truth for available models. Each entry is
`{name, model_id, provider, description}`. **The first entry is the default**
everywhere (engine fallback + UI pre-selection).

| Display name | `model_id` | Provider |
|--------------|-----------|----------|
| Llama 3.1 8B Instant (Groq) *(default)* | `llama-3.1-8b-instant` | groq |
| GPT-5.5 (OpenRouter) | `openai/gpt-5.5` | openrouter |
| Gemini 1.5 Flash (Google) | `gemini-1.5-flash` | google |
| Claude 3 Haiku (Anthropic) | `claude-3-haiku-20240307` | anthropic |

Adding a model = adding one dict here; no code changes needed if its provider
already exists.

---

## 3. Request flow (chat)

```
UI (model + persona + web_search)
        │  POST /chat
        ▼
main.py: chat_endpoint
        │  llm_engine.load_model(slm_model)
        │  if web_search: Tavily → augment message + collect sources
        ▼
LLMEngine.generate_response(message, persona)
        │  build system prompt from persona
        ▼
Provider.generate_response(system_prompt, message)
        │  vendor SDK call
        ▼
{ response, model, sources, web_note }  →  UI
```

---

## 4. The RAG API adapter — `backend/services/rag/groq_adapter.py`

Separate from the chat router, LightRAG needs its own completion function for
entity/relationship extraction and querying. This uses the **async** Groq
client:

- `AsyncGroq(api_key=…, max_retries=5)` — the retry count is raised from the
  SDK default of 2 to **5**, because LightRAG bursts several extraction calls
  and Groq's free tier (~6,000 tokens/min) returns 429s; more retries let a
  per-minute window reset instead of failing outright.
- Model is fixed to `llama-3.1-8b-instant`; `max_tokens` capped at 512.

Why a second Groq path instead of reusing the router? LightRAG requires an
`async` callable with a specific signature, and the RAG pipeline is
intentionally pinned to the one reliably-working provider.

---

## 5. The web-search API — `backend/services/research_service.py`

Powers the "Search the web" chat mode via **Tavily** (called over raw REST
with `requests`, no extra SDK):

- `web_search(query)` — POSTs to `https://api.tavily.com/search` with
  `search_depth="advanced"`, `max_results=6`, `include_answer=True`.
  Returns `None` if no `TAVILY_API_KEY`, `{"error": …}` on failure, else
  `{answer, results}`.
- `build_web_prompt(message, results)` — turns results into a
  citation-numbered prompt (`[1] title — url …`) and a parallel `sources`
  list (`{n, title, url, domain, snippet}`) for the UI to display.

The `/chat` endpoint calls these when `web_search=true`, then returns the
answer plus the `sources` list and a `web_note` explaining any fallback
(no key / request failed / no results).

---

## 6. Resilience & error handling

- **Graceful failures everywhere.** Providers return error strings instead of
  raising; the engine returns a friendly message if init fails; web search
  degrades to a plain answer with an explanatory `web_note`.
- **Lazy SDK imports** isolate provider dependencies.
- **Instance caching** avoids re-initializing SDK clients per request.
- **Raised retries** on the RAG Groq client absorb free-tier rate limits.
- **No secrets in code** — all keys via environment / `.env`.

---

## 7. Current operational status

Verified by live testing:

| Provider | Status |
|----------|--------|
| **Groq** (default) | ✅ Working — the reliable path for chat, analysis, RAG, and web-search synthesis |
| OpenRouter (GPT-5.5) | ❌ `402` — account out of credits |
| Google Gemini | ❌ `400` — invalid API key |
| Anthropic (Claude 3 Haiku) | ❌ `401` — invalid API key |
| **Tavily** (web search) | ✅ Working — returns live sources |

Because failures are graceful, selecting a broken provider produces a clear
error message in the chat rather than a crash. Functionally, **Groq + Tavily
carry the whole app today.**

---

## 8. Strengths & limitations

**Strengths**
- Clean, extensible router — new vendors slot in as a subclass + config entry.
- Uniform interface hides per-vendor quirks (Gemini's missing system role,
  Anthropic's top-level system param, OpenRouter's OpenAI compatibility).
- Fails soft at every layer; no single API outage takes the app down.
- Secrets externalized; provider clients cached.

**Limitations / recommendations**
- **3 of 4 LLM providers are non-functional** on account/key grounds — either
  renew the keys or hide those options from the model dropdown so users don't
  pick a model that only errors.
- **`max_tokens=512`** is hard-coded per provider — fine for chat, limiting
  for long output; could be parameterized.
- **No centralized retry/timeout** on the synchronous chat providers (only the
  async RAG client raises retries) — a shared policy would harden them.
- **Two Groq code paths** (sync router + async RAG adapter) — acceptable given
  LightRAG's async requirement, but worth noting as duplication.

---

*Files referenced: `backend/services/api_providers.py`,
`backend/services/llm_service.py`, `config/slm_config.py`,
`backend/services/rag/groq_adapter.py`,
`backend/services/research_service.py`, `backend/main.py`.*
