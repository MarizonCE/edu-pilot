"""
MinerU 配置模块，负责读取文档解析服务相关环境变量。
"""
from dataclasses import dataclass

from app.shared.config.common import env_str

# 问：dataclass 装饰器的作用是什么？
# 答：1. 在这里，可以自动生成构造函数，只需要直接传 base_url, api_key，不需要手写构造函数；2. ...
@dataclass
class MinerUConfig:
    base_url: str
    api_key: str
    model_version: str

mineru_config = MinerUConfig(
    base_url=env_str("MINERU_BASE_URL"),
    api_key=env_str("MINERU_API_TOKEN"),
    model_version=env_str("MINERU_MODEL_VERSION")
)

if __name__ == '__main__':
    print(mineru_config.base_url)
    print(mineru_config.api_key)