import PyPDF2
import docx
from io import BytesIO
import re


class DocumentProcessor:

    def extract_text(self, file_data, file_type):
        """Extract text from different file types"""
        if 'pdf' in file_type:
            return self._extract_pdf_text(file_data)
        elif 'word' in file_type or 'document' in file_type:
            return self._extract_docx_text(file_data)
        elif 'text' in file_type:
            return self._extract_text(file_data)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf_text(self, file_data):
        """Extract text from PDF"""
        text = ""
        pdf_file = BytesIO(file_data)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        return text

    def _extract_docx_text(self, file_data):
        """Extract text from DOCX"""
        doc_file = BytesIO(file_data)
        doc = docx.Document(doc_file)

        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        return text

    def _extract_text(self, file_data):
        """Extract text from plain text file"""
        return file_data.decode('utf-8')

    def chunk_text(self, text, chunk_size=1000, overlap=200):
        """Split text into overlapping chunks"""
        text = re.sub(r'\s+', ' ', text).strip()

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            if end < text_length:
                last_period = text.rfind('. ', start, end)
                if last_period > start + chunk_size // 2:
                    end = last_period + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap if end < text_length else text_length

        return chunks


document_processor = DocumentProcessor()
