import io
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, BinaryIO

from PyPDF2 import PdfFileWriter, PdfFileReader
from django.conf import settings
from tika import parser

import fitz
import tika

from certificates.decorators import exception_logging
from certificates.helpers import FileHelper


logger = logging.getLogger(__name__)
tika.TikaClientOnly = True


class CalibrationDataService:
    """Сервис получения калибровочных данных."""

    IMAGE_SAVE_PATH = settings.MEDIA_ROOT / 'tmp/calibration_images/'

    def __init__(self, pdf_file: BinaryIO) -> None:
        self.pdf_file = pdf_file

    @exception_logging(logger=logger)
    def __call__(self) -> Tuple[str, int, str]:
        input_pdf = PdfFileReader(self.pdf_file)
        pdf_with_first_page = PdfFileWriter()
        pdf_with_first_page.addPage(input_pdf.getPage(0))

        buffer = io.BytesIO()
        pdf_with_first_page.write(buffer)
        parsed_pdf = ParsePdfService(pdf_file=buffer.getvalue())()

        start_with_auto = FileHelper.get_first_alpha_from_string(parsed_pdf)

        calibration_certificate_path = self._save_first_pdf_page_to_image(
            pdf_file=buffer.getvalue(),
        )
        buffer.seek(0)

        return parsed_pdf, start_with_auto, calibration_certificate_path

    def _save_first_pdf_page_to_image(self, pdf_file: bytes) -> str:
        document = fitz.open(stream=pdf_file, filetype="pdf")
        page = document.loadPage(0)
        pix = page.getPixmap()

        image_name = str(uuid.uuid4())
        full_path = self.IMAGE_SAVE_PATH / f'{image_name}.png'
        image_path = FileHelper.generate_name(full_path=str(full_path), save_path=str(self.IMAGE_SAVE_PATH),
                                              file_name=image_name, file_extension='png')

        if not os.path.exists(os.path.dirname(image_path)):
            Path(image_path).mkdir(parents=True, exist_ok=True)

        pix.writePNG(image_path)
        return image_path


class SplitCertificatesService:
    """Сервис разделения PDF документа на отдельные страницы."""

    ARCHIVE_SAVE_PATH = settings.MEDIA_ROOT / 'tmp/certificates/'
    ARCHIVE_EXTENSION = 'zip'

    def __init__(self, pdf_file: BinaryIO, name_position: int) -> None:
        self.pdf_file = pdf_file
        self.name_position = name_position

    @exception_logging(logger=logger)
    def __call__(self) -> str:
        input_pdf = PdfFileReader(self.pdf_file)
        temporary_folder_name = str(uuid.uuid4())
        save_path = str(self.ARCHIVE_SAVE_PATH / temporary_folder_name)

        for i in range(input_pdf.numPages):
            pdf_with_single_page = PdfFileWriter()
            pdf_with_single_page.addPage(input_pdf.getPage(i))

            buffer = io.BytesIO()
            pdf_with_single_page.write(buffer)
            parsed_document = ParsePdfService(pdf_file=buffer.getvalue())()
            buffer.seek(0)

            certificate_name = FileHelper.trim_string_to_newline(
                string=parsed_document,
                trim_from=self.name_position,
            )
            formatted_name = FileHelper.format_file_name(certificate_name)

            full_path = f'{save_path}/{formatted_name}.pdf'

            generated_name = FileHelper.generate_name(
                full_path=full_path,
                file_name=formatted_name,
                save_path=save_path,
            )

            save_path = os.path.dirname(generated_name)

            if not os.path.exists(save_path):
                Path(save_path).mkdir(parents=True, exist_ok=True)

            with open(generated_name, "wb") as output_stream:
                pdf_with_single_page.write(output_stream)

        shutil.make_archive(save_path, self.ARCHIVE_EXTENSION, save_path)

        shutil.rmtree(save_path, ignore_errors=True)

        return save_path + '.' + self.ARCHIVE_EXTENSION


class ParsePdfService:
    """Сервис для распаршивания pdf документа."""

    def __init__(self, pdf_file: bytes) -> None:
        self.pdf_file = pdf_file

    def __call__(self) -> str:
        parsed_document = parser.from_buffer(self.pdf_file, settings.TIKA_SERVER_PATH)
        return parsed_document.get('content')
