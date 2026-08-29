import json

from app.rag.ingestion.services.service_validate_file import service_validate_file
from app.rag.ingestion.state import IngestGraphState, create_default_state
from app.shared.config.common import PROJECT_ROOT_STR


def node_validate_file(state: IngestGraphState) -> IngestGraphState:
    state = service_validate_file(state)
    return state


if __name__ == '__main__':
    test_entry_state: IngestGraphState = create_default_state(
        task_id="正常 md 文件",
        original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.md"
    )
    test_result_state = node_validate_file(test_entry_state)
    print(json.dumps(test_result_state, indent=4, ensure_ascii=False))
