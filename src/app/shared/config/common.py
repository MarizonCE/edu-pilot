"""
提供统一的环境变量配置读取与类型转换功能。
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 根目录绝对路径
PROJECT_ROOT_STR:str = "C:/Users/Marizon/Documents/PycharmProjects/edu-pilot"

def env_str(name: str, default: str = "") -> str:
    """
    读取字符串配置。
    :param name: 环境变量名称。
    :param default: 变量不存在时的默认值。
    :return: 读取到的字符串值。（str）
    """
    value = os.getenv(name)
    return value if value is not None else default


if __name__ == '__main__':
    print(env_str("CLAMAV_PORT"))
