from pathlib import Path
from app.shared.config.common import PROJECT_ROOT_STR
from app.shared.runtime.logger import logger


def load_prompt(variable_name, **kwargs) -> str:
    """
    加载提示词并渲染变量占位符
    :param variable_name: 提示词文件名
    :param kwargs: 需要渲染的变量键值对
    :return: 渲染后的最终提示词字符串
    """
    # 1. 拼接提示词路径
    if variable_name.endswith(".prompt"):
        prompt_path_obj = Path(PROJECT_ROOT_STR) / "src" / "app" / "resources" / "prompts" / f"{variable_name}"
    else:
        prompt_path_obj = Path(PROJECT_ROOT_STR) / "src" / "app" / "resources" / "prompts" / f"{variable_name}.prompt"

    # 2. 非空校验
    if not prompt_path_obj.is_file():
        logger.error(f"提示词文件不存在：{prompt_path_obj.absolute()}")
        raise FileNotFoundError(f"提示词文件不存在：{prompt_path_obj.absolute()}")

    # 3. 读取未渲染的文本提示词
    raw_prompt_text = prompt_path_obj.read_text(encoding="utf-8")

    # 4. 如果传了参数，渲染占位符；没有传参数，直接返回原文本
    if kwargs:
        rendered_prompt_text = raw_prompt_text.format(**kwargs)
        logger.debug(f"提示词渲染成功，替换变量：{list(kwargs.keys())}")
        return rendered_prompt_text
    return raw_prompt_text


if __name__ == '__main__':
    text = load_prompt("understand_image", file_title="666", pre_context="88\n", post_context="9\n\n99")
    print(text)
