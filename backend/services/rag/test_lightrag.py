import asyncio
import os

from lightrag import LightRAG, QueryParam

from backend.services.rag.openrouter_adapter import gpt55_complete
from backend.services.rag.embedding_adapter import embedding_model


WORKING_DIR = "./rag_storage"


async def initialize_rag():
    """
    Create and initialize the LightRAG instance.
    """

    rag = LightRAG(
        working_dir=WORKING_DIR,

        # GPT-5.5 through OpenRouter
        llm_model_func=gpt55_complete,
        llm_model_name="openai/gpt-5.5",

        # MiniLM embeddings
        embedding_func=embedding_model,
    )

    await rag.initialize_storages()

    return rag


def load_sample_text():

    current_dir = os.path.dirname(__file__)

    sample_path = os.path.join(
        current_dir,
        "sample.txt"
    )

    with open(sample_path, "r", encoding="utf-8") as f:
        return f.read()


async def main():

    print("=" * 60)
    print("Initializing LightRAG...")
    print("=" * 60)

    rag = await initialize_rag()

    print("✓ LightRAG initialized\n")

    print("=" * 60)
    print("Reading sample.txt")
    print("=" * 60)

    document = load_sample_text()

    print(document)
    print()

    print("=" * 60)
    print("Inserting document...")
    print("=" * 60)

    await rag.ainsert(document)

    print("✓ Document inserted")
    print()

    question = (
        "Why did GDP increase according to the document?"
    )

    print("=" * 60)
    print("QUESTION")
    print("=" * 60)

    print(question)
    print()

    print("=" * 60)
    print("Generating answer...")
    print("=" * 60)

    answer = await rag.aquery(
        question,
        param=QueryParam(
            mode="mix"
        )
    )

    print()
    print("=" * 60)
    print("ANSWER")
    print("=" * 60)

    print(answer)


if __name__ == "__main__":
    asyncio.run(main())