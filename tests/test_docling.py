from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("test.docx")

with open("test.md", "w", encoding="utf-8") as f:
    f.write(result.document.export_to_markdown())











