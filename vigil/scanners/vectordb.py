import uuid

from loguru import logger  # type: ignore

from vigil.schema import BaseScanner
from vigil.schema import ScanModel
from vigil.schema import VectorMatch
from vigil.core.vectordb import VectorDB
from vigil.registry import Registration


@Registration.scanner(name="vectordb", requires_config=True, requires_vectordb=True)
class VectorScanner(BaseScanner):
    def __init__(self, db_client: VectorDB, threshold: float, **kwargs):
        self.name = "scanner:vectordb"
        self.db_client = db_client
        self.threshold = float(threshold)
        logger.success("Loaded scanner")

    def analyze(
        self, scan_obj: ScanModel, scan_id: uuid.UUID = uuid.uuid4()
    ) -> ScanModel:
        logger.info(f'Performing scan; id="{scan_id}"')

        matches = self.db_client.query(scan_obj.prompt)
        existing_texts = []

        if (
            not matches.get("documents")
            or not matches.get("metadatas")
            or not matches.get("distances")
        ):
            raise ValueError(
                "Matches data is missing one of documents/metadatas/distances!"
            )

        else:
            # stopping mypy from complaining even though we've checked there's something above
            for match in zip(
                matches["documents"][0],  # type: ignore
                matches["metadatas"][0],  # type: ignore
                matches["distances"][0],  # type: ignore
            ):
                distance = match[2]

                if distance < self.threshold and match[0] not in existing_texts:
                    m = VectorMatch(text=match[0], metadata=match[1], distance=match[2])
                    logger.warning(
                        f'Matched vector text="{m.text}" threshold="{self.threshold}" distance="{m.distance}" id="{scan_id}"'
                    )
                    scan_obj.results.append(m.model_dump())
                    existing_texts.append(m.text)

            if len(scan_obj.results) == 0:
                logger.info(f'No matches found; id="{scan_id}"')

            return scan_obj
