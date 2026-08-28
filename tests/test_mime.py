import magic

print(magic.from_file("test_mime.py"))
print("---------------")
print(magic.from_file("test_mime.py", True))

"""
ASCII text, with CRLF line terminators
---------------
text/plain
"""
