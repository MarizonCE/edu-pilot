from pathlib import Path

import requests
from requests import Response

from app.infra.infra_config import infra_config
from app.rag.ingestion.services.config import PARSE_SERVICE_OUTPUT_DIR, MINERU_UPLOAD_URL_SUFFIX, MINERU_UPLOAD_POST_NUM
from app.rag.ingestion.state import IngestGraphState
from app.shared.config.common import PROJECT_ROOT_STR
from app.shared.runtime.logger import logger


def _get_data_and_validate(state: IngestGraphState) -> tuple[Path, Path]:
    """获取参数并校验"""
    # 1. 获取参数
    file_path_str: str = state.get("pdf_path_str", "") or state.get("pptx_path_str", "") or state.get("docx_path_str",
                                                                                                      "")
    parse_output_dir_str: str = state.get("parse_output_dir_str", "")

    # 2. file_path_str 非空检验
    if not file_path_str:
        logger.error("The file_path_str is empty. 无法继续导入文件，提前终止导入流程！")
        raise ValueError("The file_path_str is empty. 无法继续导入文件，提前终止导入流程！")

    # 3. parse_output_dir_str 非空校验
    if not parse_output_dir_str:
        parse_output_dir_str: str = PROJECT_ROOT_STR + "/" + PARSE_SERVICE_OUTPUT_DIR
        state["parse_output_dir_str"] = parse_output_dir_str
        logger.warning(f"The parse_output_dir_str is empty. 赋予其默认路径值：{parse_output_dir_str}。导入流程继续！")

    # 4. 将字符串形式的路径转化为 Path 对象，方便后续程序
    file_path_obj: Path = Path(file_path_str)
    parse_output_dir_obj: Path = Path(parse_output_dir_str)

    # 5. file_path_obj 存在性校验
    if not file_path_obj.is_file():
        logger.error(f"file_path_obj：{file_path_obj} 对应的路径不存在或路径存在但是不是文件！"
                     f"无法继续导入文件，提前终止导入流程！")
        raise FileNotFoundError(f"file_path_obj：{file_path_obj} 对应的路径不存在或路径存在但是不是文件！"
                                f"无法继续导入文件，提前终止导入流程！")

    # 6. parse_output_dir_obj 存在性校验
    if not parse_output_dir_obj.is_dir():
        parse_output_dir_obj.mkdir(parents=True, exist_ok=True)
        logger.warning(f"parse_output_dir_obj: {parse_output_dir_obj} 对应的路径不存在或路径存在但是不是目录！"
                       f"创建该目录。导入流程继续！")

    # 7. 返回校验后的参数
    return file_path_obj, parse_output_dir_obj


def _get_mineru_batch_id_and_upload_url(file_path_obj: Path) -> tuple[str, str]:
    token = infra_config.mineru.api_key
    url = infra_config.mineru.base_url + MINERU_UPLOAD_URL_SUFFIX
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "files": [
            {"name": f"{file_path_obj.name}"}
        ],
        "model_version": infra_config.mineru.model_version
    }

    response = None
    for i in range(MINERU_UPLOAD_POST_NUM):
        try:
            response = requests.post(url=url, headers=header, json=data, timeout=30)
            if response.status_code == 200:
                break
            logger.warning(f"第 {i + 1} 次尝试向 MinerU 服务器申请上传文件解析出错，"
                           f"HTTP 状态码为 {response.status_code}。")
        except requests.RequestException as e:  # 状态码为 400, 404, 500 等不会出现异常，正常返回 response
            logger.warning(f"第 {i + 1} 次向 MinerU 服务器申请上传文件解析请求失败，失败原因：{e}。")
    else:
        if response is not None:  # 这里不用 if response，因为 response 对象的布尔值会受状态码影响，4xx, 5xx 可能会返回 False
            logger.error(f"向 MinerU 服务器申请上传文件解析出错，HTTP 状态码为 {response.status_code}。"
                         f"无法继续导入文件，提前终止导入流程！")
            raise RuntimeError(f"向 MinerU 服务器申请上传文件解析出错，HTTP 状态码为 {response.status_code}。"
                               f"无法继续导入文件，提前终止导入流程！")
        else:
            logger.error(f"向 MinerU 服务器申请上传文件解析出错，错误原因未知。"
                         f"无法继续导入文件，提前终止导入流程！")
            raise RuntimeError(f"向 MinerU 服务器申请上传文件解析出错，错误原因未知。"
                               f"无法继续导入文件，提前终止导入流程！")

    if response.status_code != 200:
        logger.error(f"向 MinerU 服务器申请上传文件解析出现 HTTP 状态错误，状态码为 {response.status_code}。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise RuntimeError(f"向 MinerU 服务器申请上传文件解析出现 HTTP 状态错误，状态码为 {response.status_code}。"
                           f"无法继续导入文件，提前终止导入流程！")

    # response_dict 的格式示例为：
    # {
    #     "code": 0,
    #     "data": {
    #         "batch_id": "2bb2f0ec-a336-4a0a-b61a-241afaf9cc87",
    #         "file_urls": ["https://***"]
    #     },
    #     "msg": "ok",
    #     "trace_id": "c876cd60b202f2396de1f9e39a1b0172"
    # }
    response_dict = response.json()
    if response_dict.get("code", -1):
        logger.error(f"向 MinerU 服务器申请上传文件解析 HTTP 状态码正常，但是服务器业务状态错误，"
                     f"状态码为 {response_dict.get("code", -1)}，错误原因为 {response_dict.get("msg", "未知")}。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise RuntimeError(f"向 MinerU 服务器申请上传文件解析 HTTP 状态码正常，但是服务器业务状态错误，"
                           f"状态码为 {response_dict.get("code", -1)}，错误原因为 {response_dict.get("msg", "未知")}。"
                           f"无法继续导入文件，提前终止导入流程！")

    batch_id = response_dict.get("data", {}).get("batch_id", "")
    if not batch_id:
        logger.error(f"向 MinerU 服务器申请上传文件解析，返回的 batch_id 为空。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"向 MinerU 服务器申请上传文件解析，返回的 batch_id 为空。"
                         f"无法继续导入文件，提前终止导入流程！")

    file_upload_urls = response_dict.get("data", {}).get("file_urls", [])
    file_upload_url = ""
    if file_upload_urls:
        file_upload_url = file_upload_urls[0]

    logger.info(f"完成向 MinerU 服务器上传文件解析的申请，batch_id：{batch_id}，上传文件的预签名地址：{file_upload_url}")

    return batch_id, file_upload_url


def _upload_to_mineru():
    pass


def service_parse_file(state: IngestGraphState) -> IngestGraphState:
    """将 pdf, pptx, docx 文件通过 MinerU 解析成 md 文件"""
    # 1. 获取并校验参数
    file_path_obj: Path
    parse_output_dir_obj: Path
    file_path_obj, parse_output_dir_obj = _get_data_and_validate(state)

    # 2. 获取向 MinerU 申请上传文件解析的 batch_id 和 上传文件的预签名地址
    batch_id: str
    file_upload_url: str
    batch_id, file_upload_url = _get_mineru_batch_id_and_upload_url(file_path_obj)

    return state
