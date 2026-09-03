"""
视觉理解模型配置模块，负责读取视觉理解模型相关环境变量。
"""
from dataclasses import dataclass
from app.shared.config.common import env_str


@dataclass
class VLMConfig:
    vlm_model: str
    vlm_base_url: str
    vlm_api_key: str


vlm_config = VLMConfig(
    vlm_model=env_str("QWEN_VLM"),
    vlm_base_url=env_str("QWEN_BASE_URL"),
    vlm_api_key=env_str("QWEN_API_KEY"),
)
