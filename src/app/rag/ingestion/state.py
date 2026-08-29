import copy
import json
from typing import TypedDict


class IngestGraphState(TypedDict, total=False):
    task_id: str
    original_file_path_str: str

    # 文件类型
    is_md: bool
    is_pdf: bool
    is_pptx: bool
    is_doc: bool
    is_docx: bool
    is_jpeg: bool
    is_jpg: bool
    is_png: bool
    is_txt: bool

    # 文件路径
    md_path_str: str
    pdf_path_str: str
    pptx_path_str: str
    doc_path_str: str
    docx_path_str: str
    jpeg_path_str: str
    jpg_path_str: str
    png_path_str: str
    txt_path_str: str

    file_name: str
    file_mime: str


default_state: IngestGraphState = {
    "task_id": "",
    "original_file_path_str": "",
    "is_md": False,
    "is_pdf": False,
    "is_pptx": False,
    "is_doc": False,
    "is_docx": False,
    "is_jpeg": False,
    "is_jpg": False,
    "is_png": False,
    "is_txt": False,
    "md_path_str": "",
    "pdf_path_str": "",
    "pptx_path_str": "",
    "doc_path_str": "",
    "docx_path_str": "",
    "jpeg_path_str": "",
    "jpg_path_str": "",
    "png_path_str": "",
    "txt_path_str": "",
    "file_name": "",
    "file_mime": "",
}


def create_default_state(**kwargs) -> IngestGraphState:
    """用于更新 default_state 对象的属性"""
    new_state: IngestGraphState = copy.deepcopy(default_state)
    new_state.update(kwargs)
    return new_state


if __name__ == '__main__':
    state: IngestGraphState = create_default_state(task_id="Hello RAG", original_file_path_str="D:/md/md.md")
    print("本次生成的 state：\n{}".format(json.dumps(state, ensure_ascii=False, indent=4)))  # dumps 会生成字符串，dump 会生成文件
