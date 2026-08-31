# 导入过程中使用到的常量配置

# 文件大小限制
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MiB
DOC_PARSE_TIMEOUT = 30

# TABLE_SUFFIX = ["xls", "xlsx", "csv"]  # 目前暂时不做，后续可以用 Pandas 配合数据库存储
SUPPORTED_FILE_EXTENSIONS: set[str] = {"pdf", "pptx", "jpg", "jpeg", "png", "docx", "md"}

# 支持的扩展名 MIME
SUPPORTED_MIME_TYPES: dict[str, set[str]] = {
    "pdf": {"application/pdf"},

    "pptx": {
        "application/zip",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        'application/octet-stream'
    },

    "jpg": {"image/jpeg"},
    "jpeg": {"image/jpeg"},
    "png": {"image/png"},
    "gif": {"image/gif"},
    "webp": {"image/webp"},
    "bmp": {"image/bmp"},
    "tif": {"image/tiff"},
    "tiff": {"image/tiff"},

    "doc": {
        "application/msword",
    },

    "docx": {
        "application/zip",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },

    "md": {
        "text/plain",
        "text/markdown",
    },

    "markdown": {
        "text/plain",
        "text/markdown",
    },

    "txt": {"text/plain"},

}

# ClamAV 挂载的文档的路径
DOCKER_CLAMAV_DOC_STR = "/scan/doc"

# parse_output_dir_obj 对应的目录常量
PARSE_SERVICE_OUTPUT_DIR = "output"

# MinerU 申请上传文件的 url 后缀
MINERU_UPLOAD_URL_SUFFIX = "/file-urls/batch"

# 向 MinerU 请求上传文件的最多次数
MINERU_UPLOAD_POST_NUM = 3

# 向 MinerU 请求上传文件的超时时间
GET_MINERU_BATCH_ID_AND_UPLOAD_URL_RESPONSE_TIMEOUT = 30

# 向 MinerU 请求上传文件失败重试时间间隔
GET_MINERU_BATCH_ID_AND_UPLOAD_URL_TRY_GAP = 2

# 向 MinerU 上传文件的最多次数
MINERU_UPLOAD_FILE_NUM = 3

# 向 MinerU 上传文件的返回数据超时时间
MINERU_UPLOAD_FILE_RESPONSE_TIMEOUT = 60

# 向 MinerU 上传文件失败重试时间间隔
MINERU_UPLOAD_FILE_TRY_GAP = 2
