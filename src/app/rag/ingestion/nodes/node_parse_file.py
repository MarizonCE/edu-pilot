import os
import sys
from app.rag.ingestion.services.service_parse_file import service_parse_file
from app.rag.ingestion.state import IngestGraphState, create_default_state
from app.shared.config.common import PROJECT_ROOT_STR
from app.shared.runtime.node_and_service_log import node_log
from app.shared.utils.task_utils import add_running_task, add_done_task


@node_log("node_parse_file")
def node_parse_file(state: IngestGraphState) -> IngestGraphState:
    add_running_task(state["task_id"], sys._getframe().f_code.co_name)
    state = service_parse_file(state)
    add_done_task(state["task_id"], sys._getframe().f_code.co_name)
    return state


if __name__ == '__main__':
    # test_original_file_path_str = r"C:\Users\Marizon\Documents\PycharmProjects\edu-pilot\doc\test_file\RAG 项目.pdf"
    # test_state = create_default_state(
    #     task_id="pdf 通过 MinerU 解析测试",
    #     pdf_path_str=test_original_file_path_str,
    #     parse_output_dir_str=os.path.join(PROJECT_ROOT_STR, "output")
    # )
    # test_result = node_parse_file(test_state)
    # print(f"md_path_str:{test_result.get("md_path_str")}")

    # test_original_file_path_str = r"C:\Users\Marizon\Documents\PycharmProjects\edu-pilot\doc\test_file\渲染预览PDF（LibreOffice导出）.pdf"
    # test_state = create_default_state(
    #     task_id="复杂 pdf 通过 MinerU 解析测试",
    #     pdf_path_str=test_original_file_path_str,
    #     parse_output_dir_str=os.path.join(PROJECT_ROOT_STR, "output")
    # )
    # test_result = node_parse_file(test_state)
    # print(f"md_path_str:{test_result.get("md_path_str")}")

    # test_original_file_path_str = r"C:\Users\Marizon\Documents\PycharmProjects\edu-pilot\doc\test_file\RAG 项目（标准的 PPTX 文件）.pptx"
    # test_state = create_default_state(
    #     task_id="pptx 通过 MinerU 解析测试",
    #     pdf_path_str=test_original_file_path_str,
    #     parse_output_dir_str=os.path.join(PROJECT_ROOT_STR, "output")
    # )
    # test_result = node_parse_file(test_state)
    # print(f"md_path_str:{test_result.get("md_path_str")}")

    test_original_file_path_str = r"C:\Users\Marizon\Documents\PycharmProjects\edu-pilot\doc\test_file\RAG 项目_docx.docx"
    test_state = create_default_state(
        task_id="docx 通过 MinerU 解析测试",
        pdf_path_str=test_original_file_path_str,
        parse_output_dir_str=os.path.join(PROJECT_ROOT_STR, "output")
    )
    test_result = node_parse_file(test_state)
    print(f"md_path_str:{test_result.get("md_path_str")}")
