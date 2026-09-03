"""
图片意图识别业务模块，负责对 md 文件中的图片、上传的图片进行图意识别
"""
from pathlib import Path

from app.rag.ingestion.state import IngestGraphState
from app.shared.runtime.logger import logger


def _get_data_and_validate(state: IngestGraphState):

    # 1. 从 state 中获取参数
    md_path_str = state.get("md_path_str", "")

    # 2. md_path_str 非空校验
    if not md_path_str:
        logger.error(f"The md_path_str is empty. 无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"The md_path_str is empty. 无法继续导入文件，提前终止导入流程！")

    # 3. md_path_obj 存在性判断
    md_path_obj: Path = Path(md_path_str)
    if not md_path_obj.is_file():


def service_understand_image_and_table(state: IngestGraphState) -> IngestGraphState:
    # 1. 获取参数并校验


    return state