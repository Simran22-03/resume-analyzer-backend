from pypdf import PdfReader


def extract_text_from_pdf(file):
    """
    Extract text from an uploaded PDF resume.
    """

    reader = PdfReader(file)

    extracted_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            extracted_text.append(text)

    return "\n".join(extracted_text).strip()