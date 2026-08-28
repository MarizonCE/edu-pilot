from typing import TypedDict


class IngestGraphState(TypedDict, total=False):
    task_id: str
    original_file_path_str: str

    # 文件类型
    is_md: bool
    is_pdf: bool
    is_ppt: bool
    is_doc: bool
    is_image: bool
    is_txt: bool

    file_name: str
