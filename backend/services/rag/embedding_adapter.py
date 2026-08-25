from lightrag.utils import EmbeddingFunc

# BGE-small (v1.5) is a retrieval-tuned model that noticeably out-recalls the
# general-purpose MiniLM on numeric/finance text, while keeping the SAME 384-d
# output - so existing per-session vector stores stay dimension-compatible (no
# schema break). NOTE: vectors from the two models aren't interchangeable, so
# sessions indexed under the old model should be re-ingested for best results.
_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# The model is loaded LAZILY (on first embedding call), not at import time.
# Importing this module - and therefore importing backend.main - must not reach
# out to HuggingFace to download the model: that made the backend impossible to
# import in restricted/offline environments (and in the test suite) and slowed
# startup. It now downloads/loads only when the first document is embedded.
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


async def embedding_func(texts):
    """
    Convert list of texts into embeddings.
    """

    if isinstance(texts, str):
        texts = [texts]

    embeddings = _get_model().encode(
        texts,
        normalize_embeddings=True
    )

    return embeddings


embedding_model = EmbeddingFunc(
    embedding_dim=384,
    max_token_size=512,
    func=embedding_func,
)
