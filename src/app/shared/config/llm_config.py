"""
大语言模型配置模块，负责读取大语言模型相关环境变量。
"""
from dataclasses import dataclass
from app.shared.config.common import env_str, env_float


@dataclass
class LLMConfig:
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    llm_temperature: float


llm_config = LLMConfig(
    llm_model=env_str("DEEPSEEK_LLM"),
    llm_base_url=env_str("DEEPSEEK_BASE_URL"),
    llm_api_key=env_str("DEEPSEEK_API_KEY"),
    llm_temperature=env_float("DEEPSEEK_TEMPERATURE")
)
