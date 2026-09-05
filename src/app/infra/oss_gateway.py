from app.infra.infra_config import infra_config
from app.shared.clients.oss_client import get_oss_client


class OSSGateway:
    # 提供获取桶名称的函数
    @property
    def oss_name(self):
        return infra_config.oss.bucket_name

    # 提供获取 OSS 客户端的函数
    @property
    def minio_client(self):
        return get_oss_client()


oss_gateway = OSSGateway()
