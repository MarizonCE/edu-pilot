"""
配置聚合模块，负责将旧配置对象统一放到新的基础设施出口。
"""
from dataclasses import dataclass, field
from app.shared.config.clamav_config import ClamAVConfig, clamav_config
from app.shared.config.llm_config import LLMConfig, llm_config
from app.shared.config.mineru_config import MinerUConfig, mineru_config
from app.shared.config.vlm_config import VLMConfig, vlm_config


@dataclass
class InfrastructureConfig:
    # 问：为什么这样赋值？不直接赋值？
    clamav: ClamAVConfig = field(default_factory=lambda: clamav_config)
    mineru: MinerUConfig = field(default_factory=lambda: mineru_config)
    llm: LLMConfig = field(default_factory=lambda: llm_config)
    vlm: VLMConfig = field(default_factory=lambda: vlm_config)


infra_config = InfrastructureConfig()

if __name__ == '__main__':
    print(infra_config.clamav.host)
