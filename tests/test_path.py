from pathlib import Path

path: Path = Path("D:/Files/hello.txt.pdf")
print(path)  # 会自动调用 __str__() 得到字符串

print(path.suffix)
print(path.suffix.lower().lstrip("."))