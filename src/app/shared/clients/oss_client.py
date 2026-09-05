"""
工具模块，负责提供对象存储服务相关的辅助能力。
"""
import json

import alibabacloud_oss_v2 as oss

from app.shared.config.oss_config import oss_config
from app.shared.runtime.logger import logger

# 全局 OSS 客户端实例（单例模式，避免重复创建链接，提升性能）
_oss_client = None


# 1. 创建 OSS 客户端连接
def _create_oss_client() -> oss.Client:
    """
    创建并返回 OSS 客户端连接。
    读取配置文件中的 OSS 参数，初始化客户端连接。
    :return: 初始化完成的 OSS 客户端对象。
    """
    # 使用静态 AK（官网示例的那个是动态的，本项目由于已经静态配置了 oss_config，就使用静态了）
    credentials_provider = oss.credentials.StaticCredentialsProvider(
        access_key_id=oss_config.access_key_id,
        access_key_secret=oss_config.access_key_secret
    )

    # 加载 OSS 默认配置
    cfg = oss.config.load_default()

    # 设置凭证
    cfg.credentials_provider = credentials_provider

    # OSS Region
    cfg.region = oss_config.region

    # Endpoint
    cfg.endpoint = oss_config.endpoint

    # 创建客户端
    return oss.Client(cfg)


# 2. 定义存储桶策略
def _set_bucket_policy(bucket_name: str) -> str:
    """
    生成 OSS Bucket Policy（JSON 格式）
    即允许所有用户对桶内的所有对象执行读取操作
    :return: 序列化后的 JSON 格式访问策略字符串
    """
    policy = {
        "Version": "1",  # 这个好像不能改，是固定的？
        "Statement": [
            {
                "Effect": "Allow",  # 策略效果：允许访问
                "Principal": ["*"],  # 授权对象：所有用户
                "Action": ["oss:GetObject"],  # 授权操作：读取桶内对象
                "Resource": [f"acs:oss:*:*:{bucket_name}/*"]  # 授权范围：桶内所有对象
            }
        ]
    }
    # 将字典策略序列化为 json 字符串
    return json.dumps(policy)


# 3. 检查 Bucket 是否存在
def _bucket_exists(client: oss.Client, bucket_name: str) -> bool:
    """检查 Bucket 是否存在"""
    try:
        client.get_bucket_info(
            oss.GetBucketInfoRequest(
                bucket=bucket_name
            )
        )
    except oss.exceptions.ServiceError as e:
        if e.code == "NoSuchBucket":
            return False
        raise
    return True


# 4. 创建 Bucket + 设置访问策略
def _create_bucket_ready(client: oss.Client):
    """
    检查 OSS 桶是否存在，不存在则创建，并设置访问策略。
    确保图片上传所需的桶已就绪，避免上传失败
    :param client: 已初始化的客户端对象
    """
    bucket_name = oss_config.bucket_name
    if not _bucket_exists(client, bucket_name):
        # 创建 Bucket
        client.put_bucket(
            oss.PutBucketRequest(
                bucket=bucket_name
            )
        )

        # 设置 Bucket Policy
        client.put_bucket_policy(
            oss.PutBucketPolicyRequest(
                bucket_name=bucket_name,
                policy=_set_bucket_policy(bucket_name)
            )
        )

        logger.info(f"OSS 桶 {bucket_name} 已创建，并设置访问策略。")

    else:
        logger.info(f"OSS 桶 {bucket_name} 已存在，无需重复创建！")


# 5. 获取全局 OSS 客户端
def get_oss_client() -> oss.Client:
    """
    获取全局 OSS 客户端
    懒加载，第一次调用再创建 Client、检查 Bucket、创建 Bucket、设置 Policy
    后续调用直接复用
    :return: 全局唯一的 OSS 客户端对象
    """
    global _oss_client

    if _oss_client is None:
        logger.info("开始初始化 OSS 客户端（首次调用，执行懒加载）")
        client = _create_oss_client()
        _create_bucket_ready(client)
        _oss_client = client
        logger.info("OSS 客户端初始化完成，已就绪可使用")

    # 复用全局客户端示例，直接返回
    return _oss_client
