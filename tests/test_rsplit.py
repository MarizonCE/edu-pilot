s = "D:/Files/Heihei.txt.docx"
print(s.split("."))
print(s.rsplit("."))
print(s.rsplit(".", 1))  # 1 表示只切一次

"""
['D:/Files/Heihei', 'txt', 'docx']
['D:/Files/Heihei', 'txt', 'docx']
['D:/Files/Heihei.txt', 'docx']
"""