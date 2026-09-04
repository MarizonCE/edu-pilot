from app.shared.clients.llm_utils import get_llm_client


class LLMGateway:
    def llm_client(self, llm_model_name: str | None = None, json_mode: bool = False):
        """
        :param llm_model_name: 需要使用的大语言模型名称
        :param json_mode: 是否要以 json 格式输出
        :return: 大语言模型客户端实例
        """
        return get_llm_client(model=llm_model_name, json_mode=json_mode)


llm_gateway = LLMGateway()
