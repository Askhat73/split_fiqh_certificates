import os
from http import HTTPStatus
from unittest import mock
from unittest.mock import Mock, MagicMock

from django.conf import settings
from django.core.files import File
from django.test import TestCase
from django.urls import reverse

from certificates.models import Course, CertificateType, ParseFile, \
    ParseSession


class CourseCreateViewTest(TestCase):

    def test_url(self):
        url = reverse('home')
        self.assertEqual(url, '/')

    def test_get_success(self):
        url = reverse('home')
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'home.html')

    def test_post_success(self):
        url = reverse('home')
        course_name = 'test'
        response = self.client.post(url, data={'name': course_name})

        course = Course.objects.filter(name=course_name).first()
        self.assertIsNotNone(course)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirect_url = reverse('certificate-type-create', kwargs={'slug': course.slug})
        self.assertEqual(response.url, redirect_url)


class CertificateTypeCreateViewTest(TestCase):

    def setUp(self):
        self.course = Course.objects.create(name='test name')

    def test_url(self):
        url = reverse('certificate-type-create', kwargs={'slug': self.course.slug})
        self.assertEqual(url, '/courses/test-name/')

    def test_get_success(self):
        url = reverse('certificate-type-create', kwargs={'slug': self.course.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'certificate_type/certificate-type-create.html')

    def test_post_success(self):
        url = reverse('certificate-type-create', kwargs={'slug': self.course.slug})
        certificate_type_name = 'test'
        response = self.client.post(url, data={'name': certificate_type_name})

        certificate_type = CertificateType.objects.filter(name=certificate_type_name).first()
        self.assertIsNotNone(certificate_type)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirect_url = reverse('parse-file-create', kwargs={
            'course_slug': self.course.slug,
            'slug': certificate_type.slug,
        })
        self.assertEqual(response.url, redirect_url)


class ParseFileCreateViewTest(TestCase):

    UPLOAD_DIRECTORY = settings.BASE_DIR / 'fixtures'

    def setUp(self):
        self.course = Course.objects.create(name='test name')
        self.certificate_type = CertificateType.objects.create(
            name='test type name',
            course=self.course,
        )

    def test_url(self):
        url = reverse('parse-file-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
        })
        self.assertEqual(url, '/courses/test-name/type/test-type-name/')

    def test_get_success(self):
        url = reverse('parse-file-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'parse_file/parse-file-create.html')

    @mock.patch('certificates.services.ParsePdfService')
    def test_post_success(self, parse_pdf_service: MagicMock):
        self.parsed_data = '\n\n\n \nIbrahim\n'
        parse_pdf_service.return_value = Mock(return_value=self.parsed_data)

        url = reverse('parse-file-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
        })
        file_path = f'{self.UPLOAD_DIRECTORY}/sample.pdf'
        with open(file_path, 'rb') as file:
            response = self.client.post(url, data={'file': file})

        parsed_file = self.certificate_type.parse_files.first()
        os.remove(parsed_file.file.path)
        os.remove(parsed_file.calibration_certificate.path)
        self.assertIsNotNone(parsed_file)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirect_url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': parsed_file.pk,
        })
        self.assertEqual(response.url, redirect_url)


class ParseSessionCreateViewTest(TestCase):

    UPLOAD_DIRECTORY = settings.BASE_DIR / 'fixtures'
    NAME_POSITION = 5
    PARSE_SESSION_EXIST_MESSAGE = 'Сертификаты с такими калибровочными параметрами уже существуют'

    @mock.patch('certificates.services.ParsePdfService')
    def setUp(self, parse_pdf_service: MagicMock):
        self.parsed_data = '\n\n\n \nIbrahim\n'
        parse_pdf_service.return_value = Mock(return_value=self.parsed_data)

        self.course = Course.objects.create(name='test name')
        self.certificate_type = CertificateType.objects.create(
            name='test type name',
            course=self.course,
        )

        file_path = f'{self.UPLOAD_DIRECTORY}/sample.pdf'
        with open(file_path, 'rb') as file:
            self.parse_file = ParseFile.objects.create(
                file=File(file, name=os.path.basename(file.name)),
                certificate_type=self.certificate_type,
            )

    def tearDown(self):
        os.remove(self.parse_file.file.path)
        os.remove(self.parse_file.calibration_certificate.path)

    def test_url(self):
        url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })
        self.assertEqual(url, f'/courses/test-name/type/test-type-name/file/{self.parse_file.pk}/')

    def test_get_success(self):
        url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })
        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'parse_session/parse-session-create.html')

    @mock.patch('certificates.services.ParsePdfService')
    def test_post_success(self, parse_pdf_service: MagicMock):
        self.parsed_data = ['\n\n\n \nIbrahim\n', '\n\n\n \nIbrahim\n', '\n\n\n \nYusuf\n']
        parse_pdf_service.return_value = Mock(
            side_effect=self.parsed_data,
        )

        url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })

        response = self.client.post(url, data={'start_with': self.NAME_POSITION})

        parsed_session = self.parse_file.parse_sessions.first()
        os.remove(parsed_session.certificates.path)
        self.assertIsNotNone(parsed_session)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        redirect_url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })
        self.assertEqual(response.url, redirect_url)

    @mock.patch('certificates.services.ParsePdfService')
    def test_unique_parse_session(self, parse_pdf_service: MagicMock):
        self.parsed_data = ['\n\n\n \nIbrahim\n', '\n\n\n \nIbrahim\n', '\n\n\n \nYusuf\n']
        parse_pdf_service.return_value = Mock(
            side_effect=self.parsed_data,
        )

        url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })

        self.client.post(url, data={'start_with': self.NAME_POSITION})
        parsed_session = self.parse_file.parse_sessions.first()
        os.remove(parsed_session.certificates.path)

        response = self.client.post(url, data={'start_with': self.NAME_POSITION})

        form = response.context_data.get('form')
        self.assertIsNotNone(form)

        start_with_error = form.errors.get('start_with')
        self.assertIsNotNone(start_with_error)

        start_with_error_message = str(start_with_error.data[0].message)
        self.assertEqual(start_with_error_message, self.PARSE_SESSION_EXIST_MESSAGE)


class ParseSessionDeleteViewTest(TestCase):

    UPLOAD_DIRECTORY = settings.BASE_DIR / 'fixtures'
    NAME_POSITION = 5

    @mock.patch('certificates.services.ParsePdfService')
    def setUp(self, parse_pdf_service: MagicMock):
        self.parsed_data = '\n\n\n \nIbrahim\n'
        parse_pdf_service.return_value = Mock(return_value=self.parsed_data)

        self.course = Course.objects.create(name='test name')
        self.certificate_type = CertificateType.objects.create(
            name='test type name',
            course=self.course,
        )

        file_path = f'{self.UPLOAD_DIRECTORY}/sample.pdf'
        with open(file_path, 'rb') as file:
            self.parse_file = ParseFile.objects.create(
                file=File(file, name=os.path.basename(file.name)),
                certificate_type=self.certificate_type,
            )

        self.parsed_data = ['\n\n\n \nIbrahim\n', '\n\n\n \nIbrahim\n', '\n\n\n \nYusuf\n']
        parse_pdf_service.return_value = Mock(
            side_effect=self.parsed_data,
        )

        self.parse_session = ParseSession.objects.create(
            parse_file=self.parse_file,
            start_with=self.NAME_POSITION,
        )

    def tearDown(self):
        os.remove(self.parse_file.file.path)
        os.remove(self.parse_file.calibration_certificate.path)
        os.remove(self.parse_session.certificates.path)

    def test_url(self):
        url = reverse('parse-session-delete', kwargs={'pk': self.parse_session.pk})
        self.assertEqual(url, f'/parse-session/{self.parse_session.pk}/delete/')

    def test_post_success(self):
        url = reverse('parse-session-delete', kwargs={'pk': self.parse_session.pk})
        response = self.client.post(url)

        parsed_session = self.parse_file.parse_sessions.first()
        self.assertIsNone(parsed_session)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        redirect_url = reverse('parse-session-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })

        self.assertEqual(response.url, redirect_url)


class CourseDeleteViewTest(TestCase):

    def setUp(self,):
        self.course = Course.objects.create(name='test name')

    def test_url(self):
        url = reverse('course-delete', kwargs={'slug': self.course.slug})
        self.assertEqual(url, f'/courses/{self.course.slug}/delete/')

    def test_post_success(self):
        url = reverse('course-delete', kwargs={'slug': self.course.slug})
        response = self.client.post(url)

        course = Course.objects.filter(slug=self.course.slug).first()
        self.assertIsNone(course)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        redirect_url = reverse('home')

        self.assertEqual(response.url, redirect_url)


class CertificateTypeDeleteView(TestCase):

    def setUp(self):
        self.course = Course.objects.create(name='test name')
        self.certificate_type = CertificateType.objects.create(
            name='test type name',
            course=self.course,
        )

    def test_url(self):
        url = reverse('certificate-type-delete', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
        })
        self.assertEqual(url, f'/courses/{self.course.slug}/type/{self.certificate_type.slug}/delete/')

    def test_post_success(self):
        url = reverse('certificate-type-delete', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
        })
        response = self.client.post(url)

        certificate_type = CertificateType.objects.filter(
            course=self.course,
            slug=self.certificate_type.slug,
        ).first()
        self.assertIsNone(certificate_type)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        redirect_url = reverse('certificate-type-create', kwargs={
            'slug': self.course.slug,
        })

        self.assertEqual(response.url, redirect_url)


class ParseFileDeleteView(TestCase):

    UPLOAD_DIRECTORY = settings.BASE_DIR / 'fixtures'

    @mock.patch('certificates.services.ParsePdfService')
    def setUp(self, parse_pdf_service: MagicMock):
        self.parsed_data = '\n\n\n \nIbrahim\n'
        parse_pdf_service.return_value = Mock(return_value=self.parsed_data)

        self.course = Course.objects.create(name='test name')
        self.certificate_type = CertificateType.objects.create(
            name='test type name',
            course=self.course,
        )

        file_path = f'{self.UPLOAD_DIRECTORY}/sample.pdf'
        with open(file_path, 'rb') as file:
            self.parse_file = ParseFile.objects.create(
                file=File(file, name=os.path.basename(file.name)),
                certificate_type=self.certificate_type,
            )

    def tearDown(self):
        os.remove(self.parse_file.file.path)
        os.remove(self.parse_file.calibration_certificate.path)

    def test_url(self):
        url = reverse('parse-file-delete', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })
        self.assertEqual(url, f'/courses/{self.course.slug}/type/{self.certificate_type.slug}'
                              f'/file/{self.parse_file.pk}/delete/')

    def test_post_success(self):
        url = reverse('parse-file-delete', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.parse_file.pk,
        })
        response = self.client.post(url)

        parsed_file = self.certificate_type.parse_files.first()
        self.assertIsNone(parsed_file)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        redirect_url = reverse('parse-file-create', kwargs={
            'course_slug': self.course.slug,
            'slug': self.certificate_type.slug,
        })

        self.assertEqual(response.url, redirect_url)
