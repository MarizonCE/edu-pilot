import time
from pathlib import Path

import requests
from app.infra.infra_config import infra_config
from app.rag.ingestion.services.config import PARSE_SERVICE_OUTPUT_DIR, MINERU_UPLOAD_URL_SUFFIX, \
    MINERU_UPLOAD_POST_NUM, GET_MINERU_BATCH_ID_AND_UPLOAD_URL_RESPONSE_TIMEOUT, MINERU_UPLOAD_FILE_NUM, \
    MINERU_UPLOAD_FILE_RESPONSE_TIMEOUT, MINERU_UPLOAD_FILE_TRY_GAP, GET_MINERU_BATCH_ID_AND_UPLOAD_URL_TRY_GAP
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
    """向 MinerU 申请上传文件，获取 batch_id 和 预签名地址"""
    # 1. 基础参数
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

    # 2. 向 MinerU 申请上传文件
    response = None
    for i in range(MINERU_UPLOAD_POST_NUM):  # 多次尝试
        try:
            response = requests.post(url=url, headers=header, json=data,
                                     timeout=GET_MINERU_BATCH_ID_AND_UPLOAD_URL_RESPONSE_TIMEOUT)
            # 请求成功了就直接退出循环
            if response.status_code == 200:
                break
            # 出现 4xx 的状态码不重试
            if 400 <= response.status_code < 500:
                logger.error(f"第 {i + 1} 次尝试向 MinerU 服务器申请上传文件解析出错，"
                             f"HTTP 状态码为 {response.status_code}。无法继续导入文件，提前终止导入流程！")
                raise RuntimeError(f"第 {i + 1} 次尝试向 MinerU 服务器申请上传文件解析出错，"
                                   f"HTTP 状态码为 {response.status_code}。无法继续导入文件，提前终止导入流程！")
            logger.warning(f"第 {i + 1} 次尝试向 MinerU 服务器申请上传文件解析出错，"
                           f"HTTP 状态码为 {response.status_code}。")
        except requests.RequestException as e:  # 状态码为 400, 404, 500 等不会出现异常，正常返回 response
            logger.warning(f"第 {i + 1} 次向 MinerU 服务器申请上传文件解析请求失败，失败原因：{e}。")
        if i < MINERU_UPLOAD_POST_NUM - 1:
            time.sleep(GET_MINERU_BATCH_ID_AND_UPLOAD_URL_TRY_GAP)
    else:
        if response is not None:  # 这里不用 if response，因为 response 对象的布尔值会受状态码影响，4xx, 5xx 可能会返回 False
            logger.error(f"向 MinerU 服务器申请上传文件解析出错，HTTP 状态码为 {response.status_code}。"
                         f"无法继续导入文件，提前终止导入流程！")
            raise RuntimeError(f"向 MinerU 服务器申请上传文件解析出错，HTTP 状态码为 {response.status_code}。"
                               f"无法继续导入文件，提前终止导入流程！")
        else:
            logger.error(f"向 MinerU 服务器申请上传文件解析出错，错误原因未知。"
                         f"无法继续导入文件，提前终止导入流程！")
            raise ValueError(f"向 MinerU 服务器申请上传文件解析出错，错误原因未知。"
                             f"无法继续导入文件，提前终止导入流程！")

    # 3. 网络状态没问题，接下来判断业务状态码
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

    # 4. 网络和业务状态码都没问题，接下来抽取 batch_id 和 预签名地址
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


def _upload_to_mineru(file_upload_url: str, file_path_obj: Path) -> None:
    """向获取到的 MinerU 的预签名地址上传文件"""
    # 只需要判断网络状态码，不需要判断业务状态码，因为这里没有业务
    data = file_path_obj.read_bytes()
    upload_response = None
    with requests.Session() as session:  # 使用 Session 可以避免每次重试 put 都重新建立 TCP/TLS 连接，降低连接建立的开销、提高性能
        session.trust_env = False  # 不信任当前系统的环境
        for i in range(MINERU_UPLOAD_FILE_NUM):
            try:
                upload_response = session.put(url=file_upload_url, data=data,
                                              timeout=MINERU_UPLOAD_FILE_RESPONSE_TIMEOUT)
                if upload_response.status_code == 200:
                    return
                if 400 <= upload_response.status_code < 500:
                    break
                logger.warning(f"第 {i + 1} 尝试次向 MinerU 的预签名地址：{file_upload_url} 上传文件出现错误，网络状态码"
                               f"为 {upload_response.status_code}。")
            except requests.RequestException as e:
                logger.warning(f"第 {i + 1} 次尝试向 MinerU 的预签名地址：{file_upload_url} 上传文件出现异常，"
                               f"异常原因：{e}。")
            if i < MINERU_UPLOAD_FILE_NUM - 1:
                time.sleep(MINERU_UPLOAD_FILE_TRY_GAP)
    if upload_response is not None:
        logger.error(f"向 MinerU 的预签名地址：{file_upload_url} 上传文件出现错误，网络状态码"
                     f"为 {upload_response.status_code}。无法继续导入文件，提前终止导入流程！")
        raise RuntimeError(f"向 MinerU 的预签名地址：{file_upload_url} 上传文件出现错误，网络状态码"
                           f"为 {upload_response.status_code}。无法继续导入文件，提前终止导入流程！")
    else:
        logger.error(f"向 MinerU 的预签名地址：{file_upload_url} 上传文件出现错误，原因未知！"
                     f"无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"向 MinerU 的预签名地址：{file_upload_url} 上传文件出现错误，原因未知！"
                         f"无法继续导入文件，提前终止导入流程！")


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

    # 3. 向 MinerU 的预签名地址上传文件
    _upload_to_mineru(file_upload_url, file_path_obj)

    return state
