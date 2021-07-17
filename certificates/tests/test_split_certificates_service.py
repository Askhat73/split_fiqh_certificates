import os
import shutil
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, MagicMock

from django.conf import settings
from django.test import SimpleTestCase

from certificates.services import SplitCertificatesService


class SplitCertificatesServiceTest(SimpleTestCase):

    UPLOAD_DIRECTORY = settings.BASE_DIR / 'fixtures'
    NAME_POSITION = 5

    @mock.patch('certificates.services.ParsePdfService')
    def setUp(self, parse_pdf_service: MagicMock):
        self.parsed_data = ['\n\n\n \nIbrahim\n', '\n\n\n \nIbrahim\n', '\n\n\n \nYusuf\n']
        parse_pdf_service.return_value = Mock(
            side_effect=self.parsed_data,
        )

        file_path = f'{self.UPLOAD_DIRECTORY}/sample.pdf'
        with open(file_path, 'rb') as file_stream:
            self.certificates_archive = SplitCertificatesService(
                pdf_file=file_stream,
                name_position=self.NAME_POSITION,
            )()

        self.archive_directory = os.path.dirname(self.certificates_archive)
        self.archive_name = os.path.basename(self.certificates_archive)
        self.certificate_files = ['Ibrahim.pdf', 'Ibrahim_1.pdf', 'Yusuf.pdf']

    def tearDown(self):
        os.remove(self.certificates_archive)

    def test_success_archive_creating(self):
        """Проверяет создание архива с сертификатами."""
        archive_path = Path(self.certificates_archive)
        self.assertTrue(archive_path.exists())

    def test_pdf_creating_with_equal_name(self):
        """Проверяет создания сертификатов с одинаковыми именами."""

        extract_directory = self.archive_directory + '/' + os.path.splitext(self.archive_name)[0]
        shutil.unpack_archive(self.certificates_archive, extract_directory)
        files = os.listdir(extract_directory)

        shutil.rmtree(extract_directory, ignore_errors=True)
        self.assertListEqual(files, self.certificate_files)
        self.assertEqual(len(files), 3)


