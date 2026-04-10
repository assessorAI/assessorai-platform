from fpdf import FPDF
from docx import Document
import io
from markdown import markdown


def convert2pdf(text: str) -> io.BytesIO:
    html = markdown(text)

    pdf = FPDF()
    pdf.add_page()

    pdf_buffer = io.BytesIO()
    pdf.write_html(html)
    out = pdf.output(dest='S')
    if isinstance(out, str):
        out = out.encode('latin-1')
    pdf_buffer.write(out)
    pdf_buffer.seek(0)
    return pdf_buffer


def convert2docx(texto: str) -> io.BytesIO:
    document = Document()
    for line in texto.split('\n'):
        document.add_paragraph(line)

    docx_io = io.BytesIO()
    document.save(docx_io)
    docx_io.seek(0)
    docx_io.getvalue()
    return docx_io
