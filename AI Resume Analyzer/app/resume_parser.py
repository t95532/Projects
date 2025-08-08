from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
