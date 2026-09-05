from app.shared.clients.vlm_utils import get_vlm_client


class VLMGateway:
    def vlm_client(self, vlm_model_name: str | None = None):
        """获取视觉理解模型客户端示例"""
        return get_vlm_client(model=vlm_model_name)


vlm_gateway = VLMGateway()
