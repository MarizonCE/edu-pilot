"""
图片意图识别业务模块，负责对 md 文件中的图片、上传的图片进行图意识别
"""
import re
from pathlib import Path

from app.rag.ingestion.services.config import MODEL_SUPPORTED_IMAGE_EXTENSIONS
from app.rag.ingestion.state import IngestGraphState
from app.shared.runtime.logger import logger


def _get_data_and_validate(state: IngestGraphState) -> tuple[Path, str, Path]:
    """获取 md_path_obj, md_content, md_images_dir_obj 等参数并校验"""
    # 1. 从 state 中获取参数
    md_path_str = state.get("md_path_str", "")

    # 2. md_path_str 非空校验
    if not md_path_str:
        logger.error(f"The md_path_str is empty. 无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"The md_path_str is empty. 无法继续导入文件，提前终止导入流程！")

    # 3. md_path_obj 存在性判断
    md_path_obj: Path = Path(md_path_str)
    if not md_path_obj.is_file():
        logger.error(f"md_path_str：{md_path_str} 存在，但是其对应的文件不存在。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise FileNotFoundError(f"md_path_str：{md_path_str} 存在，但是其对应的文件不存在。"
                                f"无法继续导入文件，提前终止导入流程！")

    # 4. md_content 非空判断
    md_content = md_path_obj.read_text(encoding="utf-8")
    if not md_content:
        logger.error(f"md_path_obj 存在对应的文件，但是读取后发现里面没有内容。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"md_path_obj 存在对应的文件，但是读取后发现里面没有内容。"
                         f"无法继续导入文件，提前终止导入流程！")

    # 5. 获取解压解析结果后存放图片的地址
    md_images_dir_obj: Path = md_path_obj.parent / "images"

    return md_path_obj, md_content, md_images_dir_obj


def _scan_images(md_images_dir_obj: Path, md_content: str) -> list[tuple[str, str, tuple[str, str]]]:
    """匹配 md_content 中的图片及其附近的上下文"""
    # 1. 创建容器，用来存储图片全名、图片路径、图片附近上下文
    near_image_context: list[tuple[str, str, tuple[str, str]]] = []

    # 2. 遍历 md 文件中的每张图片，将需要的信息填入容器
    for md_image_path_obj in md_images_dir_obj.iterdir():
        # 2.1. 判断图片是否是支持的格式
        md_image_name: str = md_image_path_obj.name
        if not md_image_path_obj.suffix in MODEL_SUPPORTED_IMAGE_EXTENSIONS:
            logger.warning(f"当前文件：{md_image_name} 不是图片或不是支持的格式，不进行处理，直接跳过该文件！")
            continue

        # 2.2. 找到第一个匹配的对象
        # 这里不用这种写法 re.compile(r"!\[.*?\]\(.*? " + re.escape(md_image_name) + r".*?\)")，因为可能会匹配到 ![]描述](xxx.png) 这种结构，这不是 Markdown 中的图片格式
        image_regular = re.compile(r"!\[[^\]]*\]\([^)]*" + re.escape(md_image_name) + r"[^)]*\)")  # 还是有一些例外情况，比如引用式图片
        match = image_regular.search(md_content)
        if not match:
            logger.warning(f"{md_image_name} 图片没有被 md 内容引用，无需处理，直接跳过本张图片！")
            continue

        # 2.3. 获取图片附近的上下文并追加相关信息到容器中
        start_idx: int = match.start()
        end_idx: int = match.end()
        pre_context: str = md_content[start_idx - 100:start_idx]
        post_context: str = md_content[end_idx:end_idx + 100]  # 这里 end_idx 指向的已经是下一个字符，不再需要 + 1
        near_image_context.append((
            md_image_name,
            str(md_image_path_obj),
            (pre_context, post_context)
        ))

    return near_image_context


def service_understand_image_and_table(state: IngestGraphState) -> IngestGraphState:
    # 1. 获取参数并校验
    md_path_obj: Path
    md_content: str
    md_images_dir_obj: Path
    md_path_obj, md_content, md_images_dir_obj = _get_data_and_validate(state)
    state["md_content"] = md_content

    # 2. 获取 md_content 中的图片及其附近上下文
    near_image_context: list[tuple[str, str, tuple[str, str]]] = _scan_images(md_images_dir_obj, md_content)
    return state
