"""
文件校验业务模块，负责对上传文件安全、格式等校验
"""

from pathlib import Path
from typing import Any
from zipfile import ZipFile, BadZipFile
import magic
from PIL import Image
from docx import Document
from pptx import Presentation
from pyclamd import ClamdNetworkSocket
from pypdf import PdfReader
from app.infra.clamav_gateway import clamav_gateway
from app.rag.ingestion.services.config import MAX_FILE_SIZE_BYTES, SUPPORTED_FILE_EXTENSIONS, SUPPORTED_MIME_TYPES, \
    DOCKER_CLAMAV_DOC_STR
from app.rag.ingestion.state import IngestGraphState


def _get_data_and_validate(state: IngestGraphState) -> str:
    """获取参数并校验"""
    # 1. 从 state 中获取参数
    original_file_path_str: str = state.get("original_file_path_str", "")

    # 2. 进行非空校验
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
    if original_file_path_obj.is_symlink():
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
        original_file_actual_mime: str = magic.from_buffer(original_file_path_obj.read_bytes(),
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

    # 4. PPTX 格式可能会有特判要求
    if original_file_suffix == "pptx" and original_file_actual_mime == "application/octet-stream":
        try:
            with ZipFile(original_file_path_obj) as z:
                names = set(z.namelist())
                if "[Content_Types].xml" in names and "ppt/presentation.xml" in names:
                    return original_file_actual_mime
        except BadZipFile as e:
            raise ValueError(f"上传的 {original_file_suffix} 文件不是有效的 ZIP/OOXML 容器！"
                             f"无法继续导入文件，提前停止导入！请确保您的文件是标准文件！") from e
        except OSError as e:
            raise OSError(f"上传的 {original_file_suffix} 文件读取失败！"
                          f"无法继续导入文件，提前停止导入！请确保您的文件是标准文件！") from e

    # 5. 上传文件的实际 MIME 类型和支持的 MIME 类型不匹配
    if original_file_actual_mime not in supported_mime_types:
        raise ValueError(f"格式不支持！您上传的文件后缀为：{original_file_suffix}，"
                         f"与读取到的实际 MIME 类型 {original_file_actual_mime} 不匹配！"
                         f"无法继续导入文件，提前终止导入！")
    return original_file_actual_mime


def _virus_scan(original_file_path_obj: Path) -> None:
    """使用 ClamAV 服务进行病毒扫描"""
    try:
        # 1. 获取 pyclamd 客户端
        pyclamd_client: ClamdNetworkSocket = clamav_gateway.clamav_client

        # 2. 判断是否可以正常连接到服务
        if not pyclamd_client.ping():
            raise RuntimeError("ClamAV 病毒扫描服务不可用！"
                               "为确保安全，无法继续导入文件，提前终止导入！")

        # 3. 获取扫描结果
        clamav_result_dict: dict[Any, Any] | None = pyclamd_client.scan_file(
            DOCKER_CLAMAV_DOC_STR + "/test_file/" + original_file_path_obj.name
        )
    except Exception as e:
        raise RuntimeError("ClamAV 病毒扫描服务不可用！"
                           "为确保安全，无法继续导入文件，提前终止导入！") from e

    # 4. 判断扫描结果中是否有内容
    if clamav_result_dict:
        raise ValueError(f"疑似病毒文件！为确保安全，无法继续导入文件，提前终止导入！"
                         f"ClamAV 扫描结果：{clamav_result_dict}。")


def _validate_file_content(
        original_file_path_obj: Path,
        original_file_path_str: str,
        original_file_suffix: str
) -> None:
    """通过解析器解析文件，判断是否实际格式是否符合"""
    try:
        match original_file_suffix:

            case "pdf":
                pdf_reader: PdfReader = PdfReader(original_file_path_obj)
                _ = len(pdf_reader.pages)

            case "pptx":
                Presentation(original_file_path_str)

            case "jpg" | "jpeg" | "png":
                with Image.open(original_file_path_obj) as image:
                    image.verify()

            case "docx":
                Document(original_file_path_str)

            case "md" | "txt":
                original_file_path_obj.read_text(encoding="utf-8")

            case _:
                raise ValueError

    except Exception as e:
        raise ValueError(f"{original_file_suffix} 文件内容解析失败，可能是损坏文件或伪装文件或格式不支持，"
                         f"文件名为 {original_file_path_obj.name}。无法继续导入文件，提前终止导入！") from e


def service_validate_file(state: IngestGraphState) -> IngestGraphState:
    # 1. original_file_path_str 文件路径非空校验
    original_file_path_str: str = _get_data_and_validate(state)

    original_file_path_obj: Path = Path(original_file_path_str)

    # 2. 基础文件安全校验
    _validate_basic_file(original_file_path_obj)

    # 3. 校验文件后缀判断是否为支持的格式
    original_file_suffix: str = _get_suffix_and_validate(original_file_path_obj)

    # 4. 通过 MIME 类型校验文件格式
    original_file_actual_mime: str = _validate_mime(original_file_path_obj, original_file_suffix)

    # 5. 使用 ClamAV 进行病毒扫描
    _virus_scan(original_file_path_obj)

    # 6. 通过解析器校验文件格式
    _validate_file_content(original_file_path_obj, original_file_path_str, original_file_suffix)

    # 7. 更新类型状态
    state["is_md"] = original_file_suffix == "md"
    state["is_pdf"] = original_file_suffix == "pdf"
    state["is_pptx"] = original_file_suffix == "pptx"
    state["is_docx"] = original_file_suffix == "docx"
    state["is_jpeg"] = original_file_suffix == "jpeg"
    state["is_jpg"] = original_file_suffix == "jpg"
    state["is_png"] = original_file_suffix == "png"
    state["is_txt"] = original_file_suffix == "txt"
    state["file_name"] = original_file_path_obj.stem
    state["file_mime"] = original_file_actual_mime

    return state


"""
优化点：
1. 文件存储到 OSS，MySQL 存文件元数据，用于复用
2. 内存占用可能有点大，进行优化并做超时处理
3. 
"""
