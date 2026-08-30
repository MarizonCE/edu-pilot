import sys

from app.rag.ingestion.services.service_parse_file import service_parse_file
from app.rag.ingestion.state import IngestGraphState
from app.shared.runtime.node_and_service_log import node_log
from app.shared.utils.task_utils import add_running_task, add_done_task


@node_log("node_parse_file")
def node_parse_file(state: IngestGraphState) -> IngestGraphState:
    add_running_task(state["task_id"], sys._getframe().f_code.co_name)
    state = service_parse_file(state)
    add_done_task(state["task_id"], sys._getframe().f_code.co_name)
    return state
