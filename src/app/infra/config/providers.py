"""
配置聚合模块，负责将旧配置对象统一放到新的基础设施出口。
"""
from dataclasses import dataclass, field

from app.shared.config.clamav_config import ClamAVConfig, clamav_config


@dataclass
class InfrastructureConfig:
    # 问：为什么这样赋值？
    clamav: ClamAVConfig = field(default_factory=lambda: clamav_config)

infra_config = InfrastructureConfig()

if __name__ == '__main__':
    pass
