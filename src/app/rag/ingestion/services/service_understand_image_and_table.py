"""
图片意图识别业务模块，负责对 md 文件中的图片、上传的图片进行图意识别
"""
import asyncio
import base64
import re
from mimetypes import guess_type
from pathlib import Path
import alibabacloud_oss_v2 as oss

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from app.infra.oss_gateway import oss_gateway
from app.infra.vlm_gateway import vlm_gateway
from app.rag.ingestion.services import config
from app.rag.ingestion.services.config import MODEL_SUPPORTED_IMAGE_EXTENSIONS, OSS_IMAGES_DIR_STR, \
    OSS_UPLOAD_IMAGE_ATTEMPT_TIMES
from app.rag.ingestion.state import IngestGraphState
from app.shared.runtime.load_prompt import load_prompt
from app.shared.runtime.logger import logger
from app.shared.utils.rate_limit_utils import call_api_rate_limit


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


async def _understand_image(
        near_image_context: list[tuple[str, str, tuple[str, str]]],
        file_title: str) -> dict[str, str]:
    """调用视觉理解模型生成对应图片的摘要"""
    # 1. 获取视觉理解模型客户端实例
    vlm_client = vlm_gateway.vlm_client()

    # 2. 封装调用链
    chains = vlm_client | StrOutputParser()

    # 3. 分别处理每一张图片
    async def _understand_one_image(
            item: tuple[str, str, tuple[str, str]]) -> tuple[str, str]:
        md_image_name: str = item[0]
        md_image_path_obj: Path = Path(item[1])
        pre_context: str = item[2][0]
        post_context: str = item[2][1]

        # 3.1. 添加 API 调用速率限制
        await call_api_rate_limit()

        # 3.2. 封装提示词
        understand_image_prompt_text = load_prompt(
            variable_name="understand_image",
            file_title=file_title,
            pre_context=pre_context,
            post_context=post_context
        )
        # 可以用 Base64 编码上传也可以直接图片上传，这里图片大小比较小，选择使用 Base64 编码方式
        md_image_base64_str: str = base64.b64encode(md_image_path_obj.read_bytes()).decode("utf-8")
        messages = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": understand_image_prompt_text
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{guess_type(md_image_name)[0]};base64,{md_image_base64_str}"}
                }
            ]
        )

        # 3.3. 执行调用链
        md_image_summary = await chains.ainvoke([messages])  # 异步是 ainvoke，不要写成 invoke 了
        logger.info(f"完成：{md_image_name} 图片意图识别，识别内容：{md_image_summary}")
        return md_image_name, md_image_summary

    # 使用了 return_exceptions=True，这样某些图片出现报错也不会影响整体
    results = await asyncio.gather(*(_understand_one_image(item) for item in near_image_context),
                                   return_exceptions=True)
    image_summaries: dict[str, str] = {}
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"图片视觉理解失败：{result}")
            continue
        name, summary = result
        image_summaries[name] = summary

    return image_summaries


def _upload_image(file_title: str, near_image_context: list[tuple[str, str, tuple[str, str]]]) -> dict[str, str]:
    """将 md 中的图片上传到阿里云 OSS 服务器，并拼接访问地址。"""
    # 1. 获取 OSS 客户端对象
    oss_client = oss_gateway.oss_client

    # 2. 列举 OSS 中所有当前 file_title 下的图片
    """
    结构：
    bucket_name
      /upload-images
        /file-title
          /xxx.jpg
          /xxx.png
    """
    current_image_dir_prefix_str: str = OSS_IMAGES_DIR_STR[1:] + "/" + file_title + "/"  # 注意前面不能加 “/”
    delete_object_list: list = []
    paginator = oss_client.list_objects_v2_paginator()  # 具体使用方法：https://help.aliyun.com/zh/oss/developer-reference/list-objects-using-oss-sdk-for-python-v2?scm=20140722.S_help%40%40%E6%96%87%E6%A1%A3%40%402869962._.ID_help%40%40%E6%96%87%E6%A1%A3%40%402869962-RL_list%7EUND%7Eobjects%7EUND%7Ev2%7EUND%7Epagi-LOC_doc%7EUND%7Eab-OR_ser-PAR1_6a0b3f4917885931405942223d0098-V_4-PAR3_o-RE_new5-P0_1-P1_0&spm=a2c4g.11186623.help-search.i40
    for page in paginator.iter_page(
            oss.ListObjectsV2Request(
                bucket=oss_gateway.bucket_name,
                prefix=current_image_dir_prefix_str
            )
    ):
        for obj in page.contents:
            delete_object_list.append(oss.DeleteObject(key=obj.key))

    # 3. 删除 OSS 中所有当前 file_title 下的图片
    if delete_object_list:
        result = oss_client.delete_objects(
            oss.DeleteMultipleObjectsRequest(
                bucket=oss_gateway.bucket_name,
                encoding_type="url",  # 编码类型
                objects=delete_object_list  # 对象列表
            )
        )
        logger.info(f"对应 file_title = {file_title} 中的图片删除完成。"
                    f"status_code = {result.status_code}，request_id = {result.request_id}")

    # 4. 上传文件到 OSS，并拼接访问地址
    image_urls: dict[str, str] = {}  # {图片名: 访问图片的 url, ...}
    for md_image_name, md_image_path_str, _ in near_image_context:
        # 每张图片最多进行 OSS_UPLOAD_IMAGE_ATTEMPT_TIMES 次网络请求，失败后跳过该张图片，健壮性。
        for i in range(OSS_UPLOAD_IMAGE_ATTEMPT_TIMES):
            try:
                object_key_str: str = OSS_IMAGES_DIR_STR + "/" + file_title + "/" + md_image_name
                oss_client.put_object_from_file(
                    oss.PutObjectRequest(
                        bucket=oss_gateway.bucket_name,
                        key=object_key_str
                    ),
                    md_image_path_str
                )
                image_url = oss_gateway.build_image_url(object_key_str)
                image_urls[md_image_name] = image_url
                logger.info(f"{md_image_name} 已经上传到 OSS 服务器，访问地址：{image_url}")
                break
            except Exception as e:
                logger.warning(f"第 {i + 1} 次尝试将 {md_image_name} 图片失败，"
                               f"该图片还剩 {OSS_UPLOAD_IMAGE_ATTEMPT_TIMES - (i + 1)} 次上传机会。异常信息：{e}")
                if i + 1 == OSS_UPLOAD_IMAGE_ATTEMPT_TIMES:
                    logger.warning(f"{md_image_name} 图片上传到 OSS 失败，跳过该图片，继续运行！")
    return image_urls


def _replace_image(image_urls: dict[str, str], md_content: str, md_image_summaries: dict[str, str]) -> str:
    """将 Markdown 文件中的图片结构替换成图片描述 + 网页访问 url 的形式"""
    # 1. 图片上传全部失败或 md 文件中没有图片的情况
    if not image_urls:
        logger.warning(f"图片上传全部失败或 md 文件没有图片！直接使用原 md 内容处理！")
        return md_content

    # 2. 对 md_content 中的图片部分进行替换
    for md_image_name, md_image_url_str in image_urls.items():
        md_image_summary: str = md_image_summaries.get(md_image_name, "")
        md_image_regular = re.compile(r"!\[[^\]]*]\([^\)]*" + re.escape(md_image_name) + r"[^\)]*\)")
        md_content = md_image_regular.sub(lambda _: f"![{md_image_summary}]({md_image_url_str})", md_content)

    return md_content


def service_understand_image_and_table(state: IngestGraphState) -> IngestGraphState:
    """将 Markdown 文件中的图片和表格替换成大语言模型可以理解的形式"""
    # 1. 获取参数并校验
    md_path_obj: Path
    md_content: str
    md_images_dir_obj: Path
    md_path_obj, md_content, md_images_dir_obj = _get_data_and_validate(state)
    state["md_content"] = md_content

    # 2. 获取 md_content 中的图片及其附近上下文 -> [(图片名, 图片路径, (上文, 下文)), ...]
    near_image_context: list[tuple[str, str, tuple[str, str]]] = _scan_images(md_images_dir_obj, md_content)

    # 3. 调用视觉理解模型总结 md 文件中图片的内容 -> {图片名：大模型返回的对图片的总结描述, ...}
    md_image_summaries: dict[str, str] = asyncio.run(_understand_image(near_image_context, md_path_obj.stem))

    # 4. 将图片上传到阿里云 OSS 服务器 -> {图片名: 访问链接}
    image_urls: dict[str, str] = _upload_image(md_path_obj.stem, near_image_context)

    # 5. 将 md 文件中对应的图片结构替换 -> "...![图片摘要](图片访问 url)..."
    md_content_new = _replace_image(image_urls, md_content, md_image_summaries)

    state["md_content"] = md_content_new
    return state
