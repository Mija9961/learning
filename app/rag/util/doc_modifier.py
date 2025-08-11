import PyPDF2

def extract_text_from_pdf(file):
    """Extract text from uploaded PDF"""
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + '\n'
    return text