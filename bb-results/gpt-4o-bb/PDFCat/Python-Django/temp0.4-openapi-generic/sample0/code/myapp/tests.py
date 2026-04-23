from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile

class PDFConcatenationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_concatenate_pdfs_success(self):
        pdf1 = SimpleUploadedFile("file1.pdf", b"%PDF-1.4 file1 content", content_type="application/pdf")
        pdf2 = SimpleUploadedFile("file2.pdf", b"%PDF-1.4 file2 content", content_type="application/pdf")
        response = self.client.post('/concatenate', {'files': [pdf1, pdf2]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_concatenate_pdfs_missing_files(self):
        response = self.client.post('/concatenate', {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Invalid input or missing files.'})

    def test_concatenate_pdfs_invalid_file_type(self):
        non_pdf = SimpleUploadedFile("file.txt", b"Not a PDF", content_type="text/plain")
        response = self.client.post('/concatenate', {'files': [non_pdf]})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'All files must be PDFs.'})