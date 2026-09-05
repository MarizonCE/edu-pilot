from app.infra.infra_config import infra_config
from app.shared.clients.oss_client import get_oss_client


class OSSGateway:
    # 提供获取桶名称的函数
    @property
    def bucket_name(self):
        return infra_config.oss.bucket_name

    # 提供获取 OSS 客户端的函数
    @property
    def oss_client(self):
        return get_oss_client()

    # OSS 上传文件不会返回访问地址 -> 自己拼接 https://{bucket_name}.{endpoint}/{object_key}
    # 封装一个拼接访问地址的函数
    def build_image_url(self, object_key_str: str) -> str:
        image_url = "https://" + f"{infra_config.oss.bucket_name}.{infra_config.oss.endpoint}/{object_key_str}"
        return image_url


oss_gateway = OSSGateway()
