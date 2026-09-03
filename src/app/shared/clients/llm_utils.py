"""
负责提供大语言模型相关的辅助功能。
"""
from langchain_core.exceptions import LangChainException
from langchain_openai import ChatOpenAI
from app.shared.config.llm_config import llm_config
from app.shared.runtime.logger import logger

_DEFAULT_LLM_MODEL = "deepseek-v4-flash"
_DEFAULT_TEMPERATURE = 0.1
_llm_client_cache: dict[tuple[str, bool], ChatOpenAI] = {}


def get_llm_client(model: str | None = None, json_mode: bool = False) -> ChatOpenAI:
    """
    获取带全局缓存的 LangChain ChatOpenAI 大语言模型客户端实例
    :param model: 模型名称
    :param json_mode: 是否开启 json 输出模式，开启后返回标准的 json_object 格式
    :return: 初始化完成的 ChatOpenAI 客户端实例（优先从全局缓存获取，未命中则新建并缓存）
    """
    # 1. 确定目标大语言模型（注意优先级）
    target_llm_model = model or llm_config.llm_model or _DEFAULT_LLM_MODEL
    # 缓存键：模型名 + json 模式
    cache_key = (target_llm_model, json_mode)

    # 2. 缓存命中后，直接返回已初始化的实例，避免重复创建
    if cache_key in _llm_client_cache:
        logger.info(f"【llm 客户端】缓存命中，直接返回实例：模型 = {target_llm_model}，json_mode = {json_mode}。")
        return _llm_client_cache[cache_key]

    # 3. 核心参数校验，拦截缺失的 API 配置
    if not llm_config.llm_api_key:
        raise ValueError(f"【llm 客户端】配置缺失，请先在 .env 配置大语言模型的 api_key。")
    if not llm_config.llm_base_url:
        raise ValueError(f"【llm 客户端】配置缺失，请先在 .env 配置大语言模型的 base_url")
    logger.info(f"【llm 客户端】开始初始化新实例：模型 = {target_llm_model}，json_model = {json_mode}。")

    # 4. 配置参数
    # 关闭思维链输出，减少冗余内容（注意：只有部分模型需要，具体看对应模型官网）；这里使用的是 deepseek 的 https://api-docs.deepseek.com/zh-cn/guides/thinking_mode
    extra_body = {"thinking": {"type": "disabled"}}
    model_kwargs = {}  # OpenAI 通用参数，所有兼容 API 均支持；见 ChatOpenAI 类的介绍，当前版本在 base.py 的 3277行。
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}
        logger.debug(f"【llm 客户端】已开启 json 输出模式，模型将返回标准 json 结构。")

    # 5. 客户端初始化
    try:
        llm_client = ChatOpenAI(
            model=target_llm_model,
            temperature=llm_config.llm_temperature or _DEFAULT_TEMPERATURE,
            api_key=llm_config.llm_api_key,
            base_url=llm_config.llm_base_url,
            extra_body=extra_body,
            model_kwargs=model_kwargs
        )
    except LangChainException as e:
        raise Exception(f"【llm 客户端】模型：{target_llm_model} 初始化失败（LangChain 层面）！") from e

    # 6. 将新实例存入全局缓存，供后续调用复用
    _llm_client_cache[cache_key] = llm_client
    logger.info(f"【llm 客户端】实例初始化成功并缓存：模型 = {target_llm_model}，json_mode = {json_mode}。")

    return llm_client
