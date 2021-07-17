import os
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, MagicMock

from django.conf import settings
from django.test import SimpleTestCase

from certificates.services import CalibrationDataService


class CalibrationDataServiceTest(SimpleTestCase):

    UPLOAD_DIRECTORY = settings.BASE_DIR / 'fixtures'

    @mock.patch('certificates.services.ParsePdfService')
    def setUp(self, parse_pdf_service: MagicMock):
        self.parsed_data = '\n\n\n \nIbrahim\n'
        parse_pdf_service.return_value = Mock(return_value=self.parsed_data)

        file_path = f'{self.UPLOAD_DIRECTORY}/sample.pdf'
        with open(file_path, 'rb') as file_stream:
            self.parsed_pdf, self.start_auto_with, self.calibration_image = CalibrationDataService(
                pdf_file=file_stream,
            )()

    def tearDown(self):
        os.remove(self.calibration_image)

    def test_success(self):
        archive_path = Path(self.calibration_image)
        self.assertEqual(self.start_auto_with, 5)
        self.assertEqual(self.parsed_pdf, self.parsed_data)
        self.assertTrue(archive_path.exists())
