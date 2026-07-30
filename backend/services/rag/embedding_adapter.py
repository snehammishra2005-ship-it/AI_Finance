from sentence_transformers import SentenceTransformer
from lightrag.utils import EmbeddingFunc

# BGE-small (v1.5) is a retrieval-tuned model that noticeably out-recalls the
# general-purpose MiniLM on numeric/finance text, while keeping the SAME 384-d
# output - so existing per-session vector stores stay dimension-compatible (no
# schema break). NOTE: vectors from the two models aren't interchangeable, so
# sessions indexed under the old model should be re-ingested for best results.
model = SentenceTransformer("BAAI/bge-small-en-v1.5")


async def embedding_func(texts):
    """
    Convert list of texts into embeddings.
    """

    if isinstance(texts, str):
        texts = [texts]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )

    return embeddings


embedding_model = EmbeddingFunc(
    embedding_dim=384,
    max_token_size=512,
    func=embedding_func,
)