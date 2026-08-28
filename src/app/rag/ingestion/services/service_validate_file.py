from pathlib import Path

import magic

from app.infra.clamav_gateway import clamav_gateway
from app.rag.ingestion.services.config import MAX_FILE_SIZE_BYTES, SUPPORTED_FILE_EXTENSIONS, SUPPORTED_MIME_TYPES
from app.rag.ingestion.state import IngestGraphState


def _get_data_and_validate(state: IngestGraphState) -> str:
    original_file_path_str: str = state.get("original_file_path_str", "")
    if not original_file_path_str:
        raise ValueError("The original_file_path_str is empty. 无法继续导入文件，提前终止导入！")
    return original_file_path_str


def _validate_basic_file(original_file_path_obj: Path) -> None:
    """检查传入的文件路径是否真实存在、指向的是否为文件、是否为软连接、文件大小是否符合要求"""
    # 1. 真实路径存在与否判断
    if not original_file_path_obj.exists():
        raise FileNotFoundError(f"{original_file_path_obj} 路径中不存在真实文件，"
                                f"无法继续导入文件，提前终止导入！请确保该文件路径存在！")

    # 2. 路径指向的是否为文件判断
    if not original_file_path_obj.is_file():
        raise ValueError(f"{original_file_path_obj} 路径存在，但是指向的不是文件，"
                         f"无法继续导入文件，提前终止导入！请确保该路径指向的是文件！")

    # 3. 是否为符号链接文件判断
    if not original_file_path_obj.is_symlink():
        raise ValueError(f"{original_file_path_obj} 是符号链接文件，"
                         f"无法继续导入文件，提前终止导入！请不要上传符号链接文件，比如快捷方式！")

    # 4. 文件大小判断
    original_file_size: int = original_file_path_obj.stat().st_size  # 返回的是字节数
    if original_file_size <= 0:
        raise ValueError(f"{original_file_path_obj} 内容为空！字节数：{original_file_size}。"
                         f"无法继续导入文件，提前终止导入！请确保该文件里面存在内容！")
    elif original_file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"{original_file_path_obj} 文件过大！文件大小：{original_file_size / 1024 / 1024:.3f} MiB。"
                         f"无法继续导入文件，提前终止导入！"
                         f"请限制文件大小在 {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f} MiB 以内！")


def _get_suffix_and_validate(original_file_path_obj: Path) -> str:
    """判断格式是否支持并返回文件格式"""
    # 1. 获取文件的后缀
    original_file_suffix: str = original_file_path_obj.suffix.lstrip(".").lower()

    # 2. 通过后缀判断文件格式是否支持
    if original_file_suffix not in SUPPORTED_FILE_EXTENSIONS:
        raise ValueError(f"格式不支持！您上传的文件格式为 {original_file_suffix}。"
                         f"无法继续导入文件，提前终止导入！"
                         f"目前仅支持 {", ".join(SUPPORTED_FILE_EXTENSIONS)} 格式")
    return original_file_suffix


def _validate_mime(original_file_path_obj: Path, original_file_suffix: str, ) -> str:
    """通过 MIME 类型校验文件格式"""
    # 1. 获取上传的文件的 MIME 类型
    try:
        original_file_actual_mime: str = magic.from_file(original_file_path_obj,
                                                         mime=True)  # 读取 original_file_path_obj 指向的文件，通过文件内容或文件头判断文件真实的 MIME 类型；mime=True 表示读取 MIME 类型，而不是文件描述
    except Exception as e:
        raise ValueError(f"无法识别文件的真实类型！无法继续导入文件，提前终止导入！"
                         f"异常信息：{e}") from e

    # 2. 通过文件后缀查询支持的 MIME 类型
    # SUPPORTED_MIME_TYPES: set[str] = SUPPORTED_MIME_TYPES.get(original_file_suffix, set())  # 这样写会报错，会发生局部同名遮蔽，解决方式：一是改名；二是通过参数传入作为局部变量（如果函数内部原地修改也会影响外部可变变量）；三是 global（会把外部变量也修改）
    supported_mime_types: set[str] = SUPPORTED_MIME_TYPES.get(original_file_suffix, set())

    # 3. 上传的文件后缀没有支持的 MIME 类型
    if not supported_mime_types:
        raise ValueError(f"格式不支持！您上传的文件后缀为：{original_file_suffix}，未配置该格式的 MIME 白名单！"
                         f"无法继续导入文件，提前终止导入！")

    # 4. 上传文件的实际 MIME 类型和支持的 MIME 类型不匹配
    if original_file_actual_mime not in supported_mime_types:
        raise ValueError(f"格式不支持！您上传的文件后缀为：{original_file_suffix}，"
                         f"与读取到的实际 MIME 类型 {original_file_actual_mime} 不匹配！"
                         f"无法继续导入文件，提前终止导入！")
    return original_file_actual_mime


def _virus_scan(original_file_path_str: str) -> None:
    try:
        pyclamd_client = clamav_gateway.clamav_client
        if not pyclamd_client.ping():
            raise RuntimeError("ClamAV 病毒扫描服务不可用！"
                               "为确保安全，无法继续导入文件，提前终止导入！")
        clamav_result = pyclamd_client.scan_file(original_file_path_str)
    except Exception as e:
        raise RuntimeError("ClamAV 病毒扫描服务不可用！"
                           "为确保安全，无法继续导入文件，提前终止导入！") from e
    if clamav_result:
        raise ValueError(f"疑似病毒文件！为确保安全，无法继续导入文件，提前终止导入！"
                         f"ClamAV 扫描结果：{clamav_result}。")


def validate_and_update_state(state: IngestGraphState):
    # 2.

    # 2. 更新文件类型状态
    file_suffix = original_file_path_str.rsplit(".", 1)[-1].lower()
    match file_suffix:
        case suffix if suffix in MARKDOWN_SUFFIX:
            state["is_md"] = True
            state["is_pdf"] = False
            state["is_ppt"] = False
            state["is_doc"] = False
            state["is_image"] = False
        case suffix if suffix in PDF_SUFFIX:
            state["is_md"] = False
            state["is_pdf"] = True
            state["is_ppt"] = False
            state["is_doc"] = False
            state["is_image"] = False
        case suffix if suffix in POWERPOINT_SUFFIX:
            state["is_md"] = False
            state["is_pdf"] = False
            state["is_ppt"] = True
            state["is_doc"] = False
            state["is_image"] = False
        case suffix if suffix in DOC_SUFFIX:
            state["is_md"] = False
            state["is_pdf"] = False
            state["is_ppt"] = False
            state["is_doc"] = True
            state["is_image"] = False
        case suffix if suffix in IMAGE_SUFFIX:
            state["is_md"] = False
            state["is_pdf"] = False
            state["is_ppt"] = False
            state["is_doc"] = False
            state["is_image"] = True
        case _:
            state["is_md"] = False
            state["is_pdf"] = False
            state["is_ppt"] = False
            state["is_doc"] = False
            state["is_image"] = False
            raise ValueError(f"{file_suffix} 格式不支持，无法继续导入文件，提前终止导入！")

    # 3. 更新文件名状态
    state["file_name"] = Path(original_file_path_str).stem


def service_validate_file(state: IngestGraphState) -> IngestGraphState:
    # 1. original_file_path_str 文件路径非空校验
    original_file_path_str: str = _get_data_and_validate(state)

    original_file_path_obj: Path = Path(original_file_path_str)

    # 2. 基础文件安全校验
    _validate_basic_file(original_file_path_obj)

    # 3. 校验文件后缀判断是否为支持的格式
    original_file_suffix: str = _get_suffix_and_validate(original_file_path_obj)

    # 4. 文件 MIME 校验
    original_file_actual_mime: str = _validate_mime(original_file_path_obj, original_file_suffix)

    # 5. 使用 ClamAV 进行病毒扫描
    _virus_scan(original_file_path_str)

    return state
