# RAG Implementation

_AI in Finance · `backend/services/rag/` (`rag_service.py`, `embedding_adapter.py`, `groq_adapter.py`) + `/files`, `/rag/ask`, `/rag/reprocess`_

## 1. Overview

The RAG (Retrieval-Augmented Generation) system lets a user **ask questions
grounded in the documents they have uploaded**, with citations, instead of
relying on the model's general knowledge. It is built on **LightRAG**, which
combines vector retrieval with a **knowledge graph** of entities and
relationships extracted from the documents, so answers can draw on both
semantically-similar chunks *and* connected facts.

Two design commitments shape it:

1. **Per-session isolation** — every chat session has its own private knowledge
   base; one user's uploads are never visible to another's.
2. **Free-tier resilience** — entity extraction and answer synthesis run on
   Groq's free tier (6k tokens/min), so ingestion is serialized and failures are
   detected, reported, and retryable rather than silent.

## 2. Components

| Concern | Implementation | Detail |
|---|---|---|
| Orchestration | `LightRAG` (`lightrag-hku`) | Chunking, graph build, hybrid retrieval |
| LLM (extraction + synthesis) | Groq `llama-3.1-8b-instant` | `groq_adapter.py` · `AsyncGroq(max_retries=5)` · `temperature=0` |
| Embeddings | `BAAI/bge-small-en-v1.5` | `embedding_adapter.py` · **384-dim**, normalized · local CPU |
| Vector store | nano-vectordb | Per-session file |
| Knowledge graph | NetworkX | Entities + relationships, per-session file |
| Doc-status store | KV JSON | Tracks each document's indexing state |
| Session lifecycle | `RAGServiceManager` | In-memory LRU (32) + on-disk 7-day TTL sweep |

## 3. Ingestion flow — `ingest_document(text, file_path)`

1. **Initialize** the session's LightRAG store lazily (first use only), rooted at
   its own `workspace = session_id`.
2. **Replace, don't duplicate** — any existing document with the same filename is
   deleted first (`_delete_docs_by_filename`), so a restated report *replaces* the
   old version instead of being dropped as a duplicate and serving stale data.
3. **Structure-aware chunking** — a split character is inserted before each
   structural marker the file processor emits (`--- Page N ---`, `[Table`,
   `[Sheet:`, `[Nested table]`, `[Text box]`) and passed to
   `ainsert(split_by_character=…, split_by_character_only=False)`, so LightRAG
   chunks on document structure — keeping a financial table intact in one chunk
   rather than split across two. Falls back to a plain insert (with a warning) if
   the LightRAG build lacks the split arguments.
4. **Embed + graph** — each chunk is embedded with bge-small and passed to Groq
   for entity/relationship extraction into the knowledge graph.
5. **Verify, don't assume** — the returned `track_id` is used to read each
   document's real status. The result distinguishes:
   - `indexed: true` — fully processed
   - `duplicate: true` — identical content already present (treated as success)
   - `replaced: N` — N old versions of this filename were replaced
   - `indexed: false` + `error` — a genuine failure (e.g. rate-limit mid-extraction),
     surfaced to the user with a retry hint rather than silently swallowed.

## 4. Retrieval flow — `POST /rag/ask`

1. **Guard: does the session have documents?** Decided by reading the on-disk
   doc-status KV directly (`session_has_documents`) **without initializing** a
   store — so merely *asking* in an empty session doesn't create a persistent
   empty directory. If none: a friendly "upload a document first" reply.
2. **Hybrid query** — `aquery(mode="mix")` combines vector similarity with
   knowledge-graph traversal (LightRAG's strongest mode for multi-fact questions).
3. **Synthesis** — Groq composes the answer and cites its sources.
4. **Sanitize** — LightRAG's internal `[no-context]` sentinel is replaced with a
   clean "couldn't find anything relevant" message so the raw marker never
   reaches the user.

`get_context(question)` returns the retrieved context *without* synthesis
(`only_need_context=True`) — used by the web+document blend to combine document
context with web results in one cited answer.

## 5. Session management — `RAGServiceManager`

- **One `RAGService` per `session_id`**, each rooted at its own `workspace`. This
  is what enforces isolation: `working_dir` alone is insufficient because LightRAG
  binds storage to a process-wide in-memory dict keyed by `workspace`, so without
  a distinct workspace per session, sessions would leak into each other.
- **In-memory LRU (32 sessions)** — least-recently-used instances are finalized
  and dropped to bound memory; their on-disk data is preserved and reloaded
  transparently if the session returns.
- **Disk TTL sweep (7 days)** — on startup, session directories untouched for over
  a week are deleted so storage doesn't grow without bound.
- **`session_id` validation** — a strict regex guards against a malformed value
  being used to build a filesystem path.

## 6. Reliability features

| Concern | Handling |
|---|---|
| Silent ingestion failure | Per-doc status verified via `track_id`; failures reported, not swallowed |
| Stale data on re-upload | Same-filename doc deleted before insert (replace semantics) |
| Duplicate content | Detected and reported as an already-searchable success |
| Rate-limit mid-extraction | Groq SDK `max_retries=5`; failed docs stay retryable |
| Partially-indexed backlog | `POST /rag/reprocess` re-runs FAILED/PENDING docs via pipeline enqueue |
| Empty-session query | On-disk status check, no store init, friendly reply |
| `[no-context]` leakage | Sentinel replaced with a clean message |
| Cross-session leakage | `workspace = session_id` isolation |
| Unbounded storage/memory | LRU cap (32) + 7-day disk sweep |

## 7. Tuning / configuration

- `llm_model_max_async = 1`, `max_parallel_insert = 1` — extraction is serialized
  on purpose to stay under Groq's free-tier tokens-per-minute ceiling.
- Groq: `temperature = 0` (deterministic extraction), answer `max_tokens ≤ 512`.
- Embeddings: normalized 384-d vectors (cosine similarity), `max_token_size = 512`.

## 8. Verification

Verified end-to-end (live, in Docker) this cycle:

- **Ingest + retrieve:** a two-sheet finance workbook uploaded via `/files` was
  extracted, structure-chunked, embedded with bge-small, and indexed; `/rag/ask`
  then returned **net profit 300** (Income sheet) and **total assets 5000**
  (Balance sheet) with a citation — and **no chunking-fallback warning**,
  confirming structure-aware chunking is active and bge is serving retrieval.
- **Image → RAG:** a bank-statement image was OCR'd, ingested, and answered over —
  `/rag/ask` returned the correct closing balance ($4,935.47) with a citation to
  the source file.
- **Blend:** `get_context` fed document context into a combined web+document
  answer (the "compare my statement to current rates" case).

## 9. Diagrams

- Activity diagram — a document from upload to grounded answer:
  `rag_implementation_activity_diagram.png`
- Data flow diagram — file → answer, with the embedding/Groq services and the
  per-session store: `rag_implementation_dataflow_diagram.png`

## 10. Known limitations

- **Free-tier throughput** — serialized ingestion means a large document can take
  a while to index; very large or many-document sessions can hit rate limits
  (mitigated by `/rag/reprocess`).
- **Reprocessed-doc citations** may cite raw chunk text rather than a clean
  filename (cosmetic).
- **Answer quality** ties to the 8B model — strong for grounded factual Q&A over
  the uploaded corpus, not a substitute for a larger model on open-ended reasoning.

**Deploy note:** the embedding model (bge-small) isn't comparable with vectors
indexed under the previous model — clear `rag_storage/sessions` once and restart
so sessions re-index under bge-small.
