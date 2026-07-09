import logging

from lightrag import LightRAG, QueryParam

from backend.services.rag.embedding_adapter import embedding_model
from backend.services.rag.groq_adapter import groq_complete

logger = logging.getLogger(__name__)


class RAGService:

    def __init__(self):

        self.rag = LightRAG(
            working_dir="./rag_storage",

            llm_model_func=groq_complete,
            llm_model_name="llama-3.1-8b-instant",

            embedding_func=embedding_model,
        )

        self.initialized = False

    async def initialize(self):

        if not self.initialized:

            await self.rag.initialize_storages()

            self.initialized = True

            logger.info("LightRAG initialized")

    async def ingest_document(self, text: str):

        await self.initialize()

        await self.rag.ainsert(text)

    async def ask(self, question: str):

        await self.initialize()

        answer = await self.rag.aquery(

            question,

            param=QueryParam(
                mode="mix"
            )

        )

        return answer


rag_service = RAGService()