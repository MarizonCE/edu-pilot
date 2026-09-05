"""
阿里云 OSS 配置模块，负责读取对象存储服务相关环境变量。
"""
from dataclasses import dataclass

from app.shared.config.common import env_str


@dataclass
class OSSConfig:
    bucket_name: str
    region: str
    endpoint: str
    access_key_id: str
    access_key_secret: str

oss_config = OSSConfig(
    bucket_name=env_str("OSS_BUCKET_NAME"),
    region=env_str("OSS_REGION"),
    endpoint=env_str("OSS_ENDPOINT"),
    access_key_id=env_str("OSS_ACCESS_KEY_ID"),
    access_key_secret=env_str("OSS_ACCESS_KEY_SECRET")
)

if __name__ == '__main__':
    print(oss_config.bucket_name)
    print(oss_config.endpoint)
    print(oss_config.access_key_id)