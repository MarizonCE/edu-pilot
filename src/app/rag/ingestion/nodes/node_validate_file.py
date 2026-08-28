from app.rag.ingestion.services import service_validate_file
from app.rag.ingestion.state import IngestGraphState


def node_validate_file(state: IngestGraphState) -> IngestGraphState:
    state = service_validate_file(state)
    return state
