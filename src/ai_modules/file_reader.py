from docx import Document
import pdfplumber

def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def read_file(file_path):
    ext = file_path.lower()
    if ext.endswith(".docx"):
        return read_docx(file_path)
    elif ext.endswith(".pdf"):
        return read_pdf(file_path)
    elif ext.endswith((".jpg", ".jpeg", ".png")):
        return "Image file detected. Skipping text extraction, proceeding to QR validation."
    else: raise ValueError("Unsupported format")