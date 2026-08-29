"""
ClamAV 配置模块，负责读取病毒扫描服务相关环境变量。
"""
from dataclasses import dataclass

from app.shared.config.common import env_str


@dataclass
class ClamAVConfig:
    host: str
    port: int


clamav_config = ClamAVConfig(
    host=env_str("CLAMAV_HOST", "127.0.0.1"),
    port=int(env_str("CLAMAV_PORT", "3310"))
)

if __name__ == '__main__':
    print(clamav_config.host)
    print(clamav_config.port)
