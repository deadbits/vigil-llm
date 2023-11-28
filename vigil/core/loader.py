from loguru import logger  # type: ignore
from datasets import load_dataset  # type: ignore

from vigil.schema import DatasetEntry


class Loader:
    def __init__(self, vector_db, chunk_size=100):
        self.vector_db = vector_db
        self.chunk_size = chunk_size

    def load_dataset(self, dataset_name: str):
        buffer = []

        logger.info(f"Loading dataset: {dataset_name}")
        try:
            docs_stream = load_dataset(dataset_name, split="train", streaming=True)
        except Exception as err:
            logger.error(f"Error loading dataset: {err}")
            raise

        logger.info("Reading dataset stream ...")

        for doc in docs_stream:
            buffer.append(
                DatasetEntry(
                    text=doc["text"],
                    embeddings=doc["embeddings"],
                    metadata={"model": doc["model"]},
                )
            )
            if len(buffer) >= self.chunk_size:
                self.process_chunk(buffer)
                buffer.clear()

        if buffer:
            self.process_chunk(buffer)

        logger.info("Finished loading dataset.")

    def process_chunk(self, chunk):
        texts = [doc.text for doc in chunk]
        embeddings = [doc.embeddings for doc in chunk]
        metadatas = [doc.metadata for doc in chunk]
        self.vector_db.add_embeddings(texts, embeddings, metadatas)
        logger.info(f"Processed chunk; {len(chunk)}")
