from app.shared.clients.clamav_utils import get_clamav_client


class ClamAVGateway:
    # 提供获取 pyclamd 客户端的函数
    @property
    def clamav_client(self):
        return get_clamav_client()


clamav_gateway = ClamAVGateway()
