# 导入过程中使用到的常量配置

# 文件大小限制
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MiB
DOC_PARSE_TIMEOUT = 30

# TABLE_SUFFIX = ["xls", "xlsx", "csv"]  # 目前暂时不做，后续可以用 Pandas 配合数据库存储
SUPPORTED_FILE_EXTENSIONS: set[str] = {"pdf", "pptx", "jpg", "jpeg", "png", "docx", "doc", "md", "txt"}

# 支持的扩展名 MIME
SUPPORTED_MIME_TYPES: dict[str, set[str]] = {
    "pdf": {"application/pdf"},

    "pptx": {
        "application/zip",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
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