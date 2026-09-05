"""
文件解析业务模块，负责将上传的 pptx, pdf, docx 等文件转换成 md 格式
"""
import shutil
import time
from pathlib import Path
import requests
from app.infra.infra_config import infra_config
from app.rag.ingestion.services.config import PARSE_SERVICE_OUTPUT_DIR, MINERU_UPLOAD_URL_SUFFIX, \
    MINERU_UPLOAD_POST_NUM, GET_MINERU_BATCH_ID_AND_UPLOAD_URL_RESPONSE_TIMEOUT, MINERU_UPLOAD_FILE_NUM, \
    MINERU_UPLOAD_FILE_RESPONSE_TIMEOUT, MINERU_UPLOAD_FILE_TRY_INTERVAL_SECONDS, \
    GET_MINERU_BATCH_ID_AND_UPLOAD_URL_TRY_INTERVAL_SECONDS, MINERU_GET_EXTRACTED_RESULT_URL_SUFFIX, \
    MINERU_POLL_TIMEOUT_SECONDS, MINERU_POLL_TRY_INTERVAL_SECONDS, MINERU_DOWNLOAD_TIMEOUT_SECONDS, \
    MINERU_GET_EXTRACTED_RESULT_URL_TIMEOUT_SECONDS
from app.rag.ingestion.state import IngestGraphState
from app.shared.config.common import PROJECT_ROOT_STR
from app.shared.runtime.logger import logger
from app.shared.runtime.node_and_service_log import service_log


@service_log("_get_data_and_validate")
def _get_data_and_validate(state: IngestGraphState) -> tuple[Path, Path]:
    """获取参数并校验"""
    # 1. 获取参数
    file_path_str: str = (state.get("pdf_path_str", "") or
                          state.get("pptx_path_str", "") or
                          state.get("docx_path_str", ""))
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


@service_log("_get_mineru_batch_id_and_upload_url")
def _get_mineru_batch_id_and_upload_url(file_path_obj: Path) -> tuple[str, str, dict[str, str]]:
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
            time.sleep(GET_MINERU_BATCH_ID_AND_UPLOAD_URL_TRY_INTERVAL_SECONDS)

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
    response_dict = response.json()
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
        file_upload_url = file_upload_urls[0]  # 因为这里是单文件场景，只取第一个，如果是多文件批量上传到 MinerU 的场景

    # 5. 预签名地址非空校验
    if not file_upload_url:
        logger.error(f"从 MinerU 获取的上传文件的预签名地址为空。对应的 batch_id 为 {batch_id}。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"从 MinerU 获取的上传文件的预签名地址为空。对应的 batch_id 为 {batch_id}。"
                         f"无法继续导入文件，提前终止导入流程！")
    logger.info(f"完成向 MinerU 服务器上传文件解析的申请，batch_id：{batch_id}，上传文件的预签名地址：{file_upload_url}")
    return batch_id, file_upload_url, header


@service_log("_upload_to_mineru")
def _upload_to_mineru(file_upload_url: str, file_path_obj: Path, batch_id: str) -> None:
    """向获取到的 MinerU 的预签名地址上传文件"""
    # 只需要判断网络状态码，不需要判断业务状态码，因为这里没有业务
    # 1. 读取文件
    data = file_path_obj.read_bytes()
    upload_response = None

    # 2. 向获取到的预签名地址进行上传
    with requests.Session() as session:  # 使用 Session 可以避免每次重试 put 都重新建立 TCP/TLS 连接，降低连接建立的开销、提高性能
        session.trust_env = False  # 不信任当前系统的环境

        # 尝试 MINERU_UPLOAD_FILE_NUM 次
        for i in range(MINERU_UPLOAD_FILE_NUM):
            try:
                upload_response = session.put(url=file_upload_url, data=data,
                                              timeout=MINERU_UPLOAD_FILE_RESPONSE_TIMEOUT)

                if upload_response.status_code == 200:
                    logger.info(f"成功向从 MinerU 获取的预签名地址上传文件，对应的 batch_id：{batch_id}，"
                                f"对应的预签名地址：{file_upload_url}")
                    return
                if 400 <= upload_response.status_code < 500:
                    break

                logger.warning(f"第 {i + 1} 尝试次向 MinerU 的预签名地址：{file_upload_url} 上传文件出现错误，网络状态码"
                               f"为 {upload_response.status_code}。")

            except requests.RequestException as e:
                logger.warning(f"第 {i + 1} 次尝试向 MinerU 的预签名地址：{file_upload_url} 上传文件出现异常，"
                               f"异常原因：{e}。")

            if i < MINERU_UPLOAD_FILE_NUM - 1:
                time.sleep(MINERU_UPLOAD_FILE_TRY_INTERVAL_SECONDS)

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


@service_log("_get_extract_result")
def _get_extract_result(batch_id: str, header: dict[str, str]) -> str:
    # 1. 基础参数
    result_url = infra_config.mineru.base_url + MINERU_GET_EXTRACTED_RESULT_URL_SUFFIX + "/" + f"{batch_id}"
    start_time = time.time()

    # 2. 尝试获取解析结果
    while True:
        time_consume = time.time() - start_time

        # 1. 耗时超过 MINERU_POLL_TIMEOUT_SECONDS 就不再重试
        if time_consume >= MINERU_POLL_TIMEOUT_SECONDS:
            logger.error(f"轮询获取解析结果超时！耗时：{time_consume} 秒。对应的 batch_id：{batch_id}。"
                         f"无法继续导入文件，提前终止导入流程！")
            raise TimeoutError(f"轮询获取解析结果超时！耗时：{time_consume} s。对应的 batch_id：{batch_id}。"
                               f"无法继续导入文件，提前终止导入流程！")

        # 2. 没有超时时：
        try:
            poll_result = requests.get(url=result_url, headers=header,
                                       timeout=MINERU_GET_EXTRACTED_RESULT_URL_TIMEOUT_SECONDS)
        except Exception as e:
            logger.warning(f"获取解析结果出现网络波动，异常信息：{e}，{MINERU_POLL_TRY_INTERVAL_SECONDS} 秒后重试！")
            time.sleep(MINERU_POLL_TRY_INTERVAL_SECONDS)
            continue

        # 3. 正常返回 poll_result 时，进行网络状态码判定
        status_code = poll_result.status_code
        if status_code != 200:
            if 500 <= status_code < 600:
                logger.warning(f"从 MinerU 获取文件解析结果出现网络状态错误，状态码为 {status_code}。"
                               f"等待服务器修复，{MINERU_POLL_TRY_INTERVAL_SECONDS} 秒后重试！")
                time.sleep(MINERU_POLL_TRY_INTERVAL_SECONDS)
                continue
            else:
                logger.error(f"从 MinerU 获取文件解析结果服务器访问报错，状态码为 {status_code}，错误无法修复！"
                             f"无法继续导入文件，提前终止导入流程！")
                raise RuntimeError(f"从 MinerU 获取文件解析结果服务器访问报错，状态码为 {status_code}，错误无法修复！"
                                   f"无法继续导入文件，提前终止导入流程！")

        # 4. 网络状态码正常，接下来进行业务状态码判定
        poll_result_dict = poll_result.json()
        # poll_result_dict 长这样：
        # {
        #     "code": 0,
        #     "data": {
        #         "batch_id": "2bb2f0ec-a336-4a0a-b61a-241afaf9cc87",
        #         "extract_result": [
        #             {
        #                 "file_name": "example.pdf",
        #                 "state": "done",
        #                 "err_msg": "",
        #                 "full_zip_url": "https://cdn-mineru.openxlab.org.cn/pdf/018e53ad-d4f1-475d-b380-36bf24db9914.zip"
        #             },
        #             {
        #                 "file_name": "demo.pdf",
        #                 "state": "running",
        #                 "err_msg": "",
        #                 "extract_progress": {
        #                     "extracted_pages": 1,
        #                     "total_pages": 2,
        #                     "start_time": "2025-01-20 11:43:20"
        #                 }
        #             }
        #         ]
        #     },
        #     "msg": "ok",
        #     "trace_id": "c876cd60b202f2396de1f9e39a1b0172"
        # }
        business_status_code = poll_result_dict.get("code", -1)
        if business_status_code != 0:
            # 官网中有各种代码出现的原因，生成环境可写更详细的判断！
            logger.error(f"从 MinerU 获取解析结果出现业务状态报错，业务状态码为 {business_status_code}。"
                         f"错误信息：{poll_result_dict.get("msg", "未知")}。无法继续导入文件，提前终止导入流程！")
            raise RuntimeError(f"从 MinerU 获取解析结果出现业务状态报错，业务状态码为 {business_status_code}。"
                               f"错误信息：{poll_result_dict.get("msg", "未知")}。无法继续导入文件，提前终止导入流程！")

        # 5. 网络状态码和业务状态码都正常，获取解析结果
        extract_result_list = poll_result_dict.get("data", {}).get("extract_result", [])
        if not extract_result_list:
            logger.warning("获取到的解析结果列表 extract_result_list 为空，跳过本次 poll。"
                           f"{MINERU_POLL_TRY_INTERVAL_SECONDS} 秒后重新获取！")
            time.sleep(MINERU_POLL_TRY_INTERVAL_SECONDS)
            continue
        extract_result = extract_result_list[0]

        # 6. 解析结果状态判定
        extract_result_state: str = extract_result.get("state", "")
        if extract_result_state == "done":
            full_zip_url = extract_result.get("full_zip_url")
            if not full_zip_url:
                logger.error(f"从 MinerU 获取文件解析结果，任务已经完成，但是 full_zip_url 中没有地址！"
                             f"对应的 batch_id 为 {batch_id}。无法继续导入文件，提前终止导入流程！")
                raise ValueError(f"从 MinerU 获取文件解析结果，任务已经完成，但是 full_zip_url 中没有地址！"
                                 f"对应的 batch_id 为 {batch_id}。无法继续导入文件，提前终止导入流程！")
            return full_zip_url
        elif extract_result_state == "failed":
            logger.error(f"从 MinerU 获取文件解析结果，解析失败！对应的 batch_id 为 {batch_id}。"
                         f"无法继续导入文件，提前终止导入！")
            raise RuntimeError(f"从 MinerU 获取文件解析结果，解析失败！对应的 batch_id 为 {batch_id}。"
                               f"无法继续导入文件，提前终止导入！")
        else:
            logger.warning(f"从 MinerU 获取文件解析结果，本次没有获取到结果，"
                           f"{MINERU_POLL_TRY_INTERVAL_SECONDS} 秒后继续尝试！")
            time.sleep(MINERU_POLL_TRY_INTERVAL_SECONDS)
            continue
    raise RuntimeError("Unexpected unreachable state")


@service_log("_download_and_extract")
def _download_and_extract(zip_url: str, parse_output_dir_obj: Path, file_name: str) -> Path:
    """下载、解压并重命名文件"""
    # 1. 下载
    download_response = requests.get(zip_url, timeout=MINERU_DOWNLOAD_TIMEOUT_SECONDS)

    if download_response.status_code != 200:
        logger.error(f"从 MinerU 下载解析后的结果 zip 文件出错，网络状态码为 {download_response.status_code}"
                     f"zip_url 为 {zip_url}。无法继续导入文件，提前终止导入流程！")
        raise RuntimeError(f"从 MinerU 下载解析后的结果 zip 文件出错，网络状态码为 {download_response.status_code}"
                           f"zip_url 为 {zip_url}。无法继续导入文件，提前终止导入流程！")

    result_zip_file_obj: Path = parse_output_dir_obj / f"{file_name}.zip"  # 路径记得写全，不要忘了后缀
    result_zip_file_obj.write_bytes(download_response.content)

    # 2. 解压
    result_zip_extract_dir: Path = parse_output_dir_obj / file_name
    if result_zip_extract_dir.is_dir():
        shutil.rmtree(result_zip_extract_dir)
    result_zip_extract_dir.mkdir(parents=True, exist_ok=True)  # 如果已经存在同名文件（包括后缀），也不能创建目录
    shutil.unpack_archive(result_zip_file_obj, result_zip_extract_dir)

    # 3. md 文件重命名与原文件同名
    # 注意列表里的路径是否是绝对路径取决于 result_zip_extract_dir
    extracted_md_path_obj_list: list[Path] = list(result_zip_extract_dir.rglob("*.md"))
    if not extracted_md_path_obj_list:
        logger.error(f"从 MinerU 下载的文件解析结果 zip 文件解压后里面没有 md 文件。"
                     f"无法继续导入文件，提前终止导入流程！")
        raise ValueError(f"从 MinerU 下载的文件解析结果 zip 文件解压后里面没有 md 文件。"
                         f"无法继续导入文件，提前终止导入流程！")

    for current_extracted_md_path_obj in extracted_md_path_obj_list:
        if current_extracted_md_path_obj.stem == file_name:
            logger.info(f"从 MinerU 下载的文件解析结果解压后的 md 文件与原上传文件同名，直接返回！")
            return current_extracted_md_path_obj

    for current_extracted_md_path_obj in extracted_md_path_obj_list:
        if current_extracted_md_path_obj.stem == "full":
            extracted_md_path_obj: Path = current_extracted_md_path_obj
            break
    else:
        extracted_md_path_obj: Path = extracted_md_path_obj_list[0]
    extracted_md_path_obj: Path = extracted_md_path_obj.rename(extracted_md_path_obj.parent / f"{file_name}.md")

    return extracted_md_path_obj


@service_log("service_parse_file")
def service_parse_file(state: IngestGraphState) -> IngestGraphState:
    """将 pdf, pptx, docx 文件通过 MinerU 解析成 md 文件。"""
    # 1. 获取并校验参数
    file_path_obj: Path
    parse_output_dir_obj: Path
    file_path_obj, parse_output_dir_obj = _get_data_and_validate(state)

    # 2. 获取向 MinerU 申请上传文件解析的 batch_id 和 上传文件的预签名地址
    batch_id: str
    file_upload_url: str
    batch_id, file_upload_url, header = _get_mineru_batch_id_and_upload_url(file_path_obj)

    # 3. 向 MinerU 的预签名地址上传文件
    _upload_to_mineru(file_upload_url, file_path_obj, batch_id)

    # 4. 获取 MinerU 解析结果
    full_zip_url = _get_extract_result(batch_id, header)

    # 5. 下载、解压并重命名结果中的 md 文件
    md_path_obj: Path = _download_and_extract(full_zip_url, parse_output_dir_obj, file_path_obj.stem)

    # 6. 判断该 md 文件里面是否有图片并更新状态
    md_images_dir_obj: Path = md_path_obj.parent / "images"
    if not md_images_dir_obj.is_dir():
        state["is_image_in_md"] = False
    state["is_image_in_md"] = True
    state["md_path_str"] = str(md_path_obj)

    return state
