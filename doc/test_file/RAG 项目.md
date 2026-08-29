# RAG 项目

## 文件校验节点

1. 获取 local_file_path
1. 非空校验
1. 判断文件类型并存入  不能处理的类型
1. 获取文件名并存入



_validate_basic_file(path: Path) -> None:

1. 文件存在判断 Path.exists() 不存在则报错
2. 文件判断 Path.is_file() 不是则报错
3. 软连接判断 Path.is_symlink() 是则报错
4. 文件大小判断Path.stat().st_size <=0 则文件为空，大于设定则报错

_get_suffix_and_validate(path: Path) -> str

1. 获取文件后缀并返回 Path.suffix.lstrip(".").lower()
2. 判断是否在支持的格式里，不在-> 报错格式不支持

_validate_mime(path: Path, suffix: str) -> str:

"""防止仅修改扩展名的伪装文件"""

1. 获取上传的文件的MIME类型

try:

1. actual_MIME = magic.from_file(str(path), mime=True)

except:无法识别文件真实类型

2. 获取该类型文件支持的 MIME类型
3. 如果没找到该文件格式-> 报错，格式不支持，未配置该格式的 MIME 白名单
4. 如果实际 MIME 和 支持的 MIME 不匹配 -> 报错，文件类型校验失败。
5. 返回真实的 MIME

_virus_scan(path: Path) -> None

1. 获取扫描结果

try:

1. 获取 pyclamd 客户端
2. client.ping() 服务正常 -> True 服务不可用 -> False
3. client.scan_file(str(path: Path)) -> result

except -> 病毒扫描服务不可用，拒绝继续处理 from e

2. 检查扫描结果：result->  检测到病毒 dict | 没检测到病毒 None

_validate_file_content(path: Path, suffix: str) -> None:

实际格式解析（专用解析器）

try:

1. pdf : from pypdf import PdfReader  pdfRead(str(path))  len(read.pages) 强制触发 PDF 解析 因为 PDF Reader解析有部分内容是 laze parsing
2. docx：from docx import Document Document(str(path))
3. pptx: from pptx import Presentation Presentation(str(path))
4. 图片：FROM PIL import  Image Image.open(path) as image: image.verify()
5. md： path.read_text(encoding="utf-8")
6. txt 同 md
7. doc：import subprocess subprocess.run(["antiword", str(path)], check=True, capture_output=True)

except: suffix 文件内容解析失败，可能是损坏文件或伪装文件， {path.name}

