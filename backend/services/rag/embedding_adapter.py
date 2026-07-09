from sentence_transformers import SentenceTransformer
from lightrag.utils import EmbeddingFunc

# Load once when application starts
model = SentenceTransformer("all-MiniLM-L6-v2")


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