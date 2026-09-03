"""
负责提供视觉理解模型相关的辅助功能。
"""
from langchain_core.exceptions import LangChainException
from langchain_openai import ChatOpenAI
from app.shared.config.vlm_config import vlm_config

_DEFAULT_VLM_MODEL = "qwen3.8-max"


def get_vlm_client(model: str | None = None) -> ChatOpenAI:
    target_vlm_model = model or vlm_config.vlm_model or _DEFAULT_VLM_MODEL
    extra_body = {"enable_thinking": True}
    # 官网上没找到视觉理解的情况是否支持调整 Temperature，这里先不调
    try:
        vlm_client = ChatOpenAI(
            model=target_vlm_model,
            api_key=vlm_config.vlm_api_key,
            base_url=vlm_config.vlm_base_url,
            extra_body=extra_body
        )
    except LangChainException as e:
        raise Exception(f"【vlm 客户端】实例创建失败（LangChain 层面）！") from e
    return vlm_client
