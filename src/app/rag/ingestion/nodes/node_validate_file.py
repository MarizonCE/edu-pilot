import json
import sys

from app.rag.ingestion.services.service_validate_file import service_validate_file
from app.rag.ingestion.state import IngestGraphState, create_default_state
from app.shared.config.common import PROJECT_ROOT_STR
from app.shared.runtime.node_and_service_log import node_log
from app.shared.utils.task_utils import add_running_task


@node_log("node_validate_file")
def node_validate_file(state: IngestGraphState) -> IngestGraphState:
    add_running_task(state["task_id"], sys._getframe().f_code.co_name)  # 使用 inspect.currentframe().f_code.co_name 也可以
    state = service_validate_file(state)
    add_running_task(state["task_id"], sys._getframe().f_code.co_name)
    return state


if __name__ == '__main__':
    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="正常 md 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.md"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="正常 pdf 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.pdf"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="正常 pptx 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目（标准的 PPTX 文件）.pptx"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="豆包生成的 pptx 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.pptx"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))
    #
    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="正常 docx 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.docx"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))
    #

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="不支持的 doc 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 测试.doc"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="空文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目（空文件）.txt"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="正常 jpg 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/001.jpg"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="正常 png 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/001.png"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="路径为空",
    #     original_file_path_str=""
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="不存在的文件",
    #     original_file_path_str="D:test.txt.txt"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="路径指向的不是文件",
    #     original_file_path_str="C:/Users"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))
    #
    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="路径是快捷方式",
    #     original_file_path_str=r"C:\Users\Marizon\Desktop\豆豆包.lnk"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="空文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目（空文件）.txt"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="大文件",
    #     original_file_path_str=r"C:\Users\Marizon\Documents\ChromeDownloads\WorkBuddy-win32-x64-user-5.3.14.36279234-825709d4.exe"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="不支持的 ppt 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目（不支持的格式）.ppt"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="修改过扩展名的文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目（修改过后缀的格式）.pdf"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="测试 Docker 容器未开启的情况",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.docx"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="测试豆包生成的 docx 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/复杂DOCX测试样本.docx"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    test_entry_state: IngestGraphState = create_default_state(
        task_id="测试 LibreOffice 导出的 pdf 文件",
        original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/渲染预览PDF（LibreOffice导出）.pdf"
    )
    test_result_state = node_validate_file(test_entry_state)
    print(json.dumps(test_result_state, indent=4, ensure_ascii=False))


