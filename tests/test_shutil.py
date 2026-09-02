import shutil

# 1. 复制 src 文件到 dst 文件夹（要求 dst 文件夹已经存在），否则报错
# shutil.copy("test_file_a.txt", "test_dir_a/")

# 2. 和 copy 类似，但是尽量保留元数据
# shutil.copy("test_file_b.txt", "test_dir_a/")

# 3. 复制整个目录的文件到另外一个目录
# shutil.copytree("test_dir_a", "test_dir_b", dirs_exist_ok=True)

# 4. 移动/重命名文件或目录
# shutil.move("test_file_c.txt", "test_dir_a")  # 移动到 test_dir_a
# shutil.move("test_file_a.txt", "test_file_d.txt")  # 重命名为 test_file_d.txt

# 5. 递归删除整个目录
# shutil.rmtree("test_dir_a")

# 6. 打包成压缩包，第一个参数是压缩包文件名称，第二个参数是压缩格式，第三个参数是要进行压缩的文件
# shutil.make_archive("test_dir_b_zip", "zip", "test_dir_b")

# 7. 解压，第一个参数是压缩包文件名称，第二个参数是解压后的文件名称
shutil.unpack_archive("test_dir_b_zip.zip", "test_dir_b_unpack")