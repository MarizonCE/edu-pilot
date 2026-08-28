"""
工具模块，负责提供 ClamAV 相关的辅助功能。
"""

import pyclamd

from app.shared.config.clamav_config import clamav_config


def get_clamav_client() -> pyclamd.ClamdNetworkSocket:
    return pyclamd.ClamdNetworkSocket(
        clamav_config.host,
        clamav_config.port
    )
