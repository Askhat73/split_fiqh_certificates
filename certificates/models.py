import os
from functools import cached_property

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from pytils.translit import slugify

from certificates.services import CalibrationDataService, \
    SplitCertificatesService


class Course(models.Model):
    """Курс."""

    slug = models.SlugField()
    name = models.CharField(max_length=150, verbose_name='Название курса', unique=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def get_absolute_url(self) -> str:
        return reverse('course-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CertificateType(models.Model):
    """Тип сертификата (на русском, на арабском и т.д.)."""

    slug = models.SlugField()
    name = models.CharField(max_length=150, verbose_name='Тип сертификата')
    course = models.ForeignKey('Course', on_delete=models.CASCADE,
                               related_name='certificate_types', verbose_name='Курс')

    class Meta:
        verbose_name = 'Тип сертификата'
        verbose_name_plural = 'Типы сертификата'
        unique_together = ['name', 'course_id']

    def get_absolute_url(self) -> str:
        return reverse('certificate-type-detail', kwargs={
            'course_slug': self.course.slug,
            'slug': self.slug,
        })

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ParseFile(models.Model):
    """Файл с сертификатами для разделения."""

    file = models.FileField(upload_to='parse_files',
                            verbose_name='Файл для разделения сертификатов')
    certificate_type = models.ForeignKey('CertificateType', on_delete=models.CASCADE,
                                         related_name='parse_files', verbose_name='Тип сертификата')

    calibration_certificate = models.ImageField(verbose_name='Сертификат для калибровки')
    parsed_page = models.TextField(verbose_name='Распаршенная страница')
    start_with_auto = models.IntegerField(verbose_name='Начало имени в сертификате (определяется автоматически)',
                                          validators=[MinValueValidator(0)])

    def get_absolute_url(self) -> str:
        return reverse('parse-file-detail', kwargs={
            'course_slug': self.certificate_type.course.slug,
            'slug': self.certificate_type.slug,
            'pk': self.pk,
        })

    @cached_property
    def file_name(self) -> str:
        return os.path.basename(self.file.name)

    @cached_property
    def trimmed_parsed_page(self) -> str:
        """Обрезанная распаршенная страница."""
        return self.parsed_page[self.start_with_auto:]

    def save(self, *args, **kwargs):
        if not self.parsed_page or not self.start_with_auto or not self.calibration_certificate:
            self.parsed_page, self.start_with_auto, tmp_file \
                = CalibrationDataService(pdf_file=self.file.file.file)()
            self.calibration_certificate.name = os.path.relpath(tmp_file, settings.MEDIA_ROOT)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.file_name


class ParseSession(models.Model):

    parse_file = models.ForeignKey('ParseFile', on_delete=models.CASCADE,
                                   related_name='parse_sessions', verbose_name='Файл с сертификатами')
    start_with = models.IntegerField(verbose_name='Начало имени в сертификате',
                                     validators=[MinValueValidator(0)])
    certificates = models.FileField(upload_to='certificates', verbose_name='Архив с сертификатами')

    class Meta:
        unique_together = ['parse_file_id', 'start_with']

    def get_absolute_url(self) -> str:
        return reverse('parse-file-detail', kwargs={
            'course_slug': self.parse_file.certificate_type.course.slug,
            'slug': self.parse_file.certificate_type.slug,
            'pk': self.parse_file.pk,
        })

    def save(self, *args, **kwargs):
        if not self.certificates:
            certificates_archive = SplitCertificatesService(
                pdf_file=self.parse_file.file.file,
                name_position=self.start_with,
            )()
            self.certificates.name = os.path.relpath(certificates_archive, settings.MEDIA_ROOT)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.parse_file.file_name} - {self.start_with}'
