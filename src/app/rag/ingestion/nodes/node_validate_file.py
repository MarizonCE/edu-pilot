import json

from app.rag.ingestion.services.service_validate_file import service_validate_file
from app.rag.ingestion.state import IngestGraphState, create_default_state
from app.shared.config.common import PROJECT_ROOT_STR


def node_validate_file(state: IngestGraphState) -> IngestGraphState:
    state = service_validate_file(state)
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
    #     task_id="正常 txt 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目.txt"
    # )
    # test_result_state = node_validate_file(test_entry_state)
    # print(json.dumps(test_result_state, indent=4, ensure_ascii=False))

    # test_entry_state: IngestGraphState = create_default_state(
    #     task_id="不支持的 doc 文件",
    #     original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 测试.doc"
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

    test_entry_state: IngestGraphState = create_default_state(
        task_id="空文件",
        original_file_path_str=PROJECT_ROOT_STR + "/doc/test_file/RAG 项目（空文件）.txt"
    )
    test_result_state = node_validate_file(test_entry_state)
    print(json.dumps(test_result_state, indent=4, ensure_ascii=False))