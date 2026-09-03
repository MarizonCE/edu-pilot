import sys

from app.rag.ingestion.services.service_understand_image_and_table import service_understand_image_and_table
from app.rag.ingestion.state import IngestGraphState
from app.shared.runtime.node_and_service_log import node_log
from app.shared.utils.task_utils import add_done_task, add_running_task

@node_log("node_understand_image_and_table")
def node_understand_image_and_table(state: IngestGraphState) -> IngestGraphState:
    add_running_task(state["task_id"], sys._getframe().f_code.co_name)
    state = service_understand_image_and_table(state)
    add_done_task(state["task_id"], sys._getframe().f_code.co_name)
    return state


if __name__ == '__main__':
    pass
