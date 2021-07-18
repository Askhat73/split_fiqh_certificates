from django.db import IntegrityError
from django.db.models import QuerySet
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView

from certificates.models import Course, CertificateType, ParseFile, \
    ParseSession


class CourseCreateView(CreateView):

    model = Course
    fields = ['name']
    template_name = 'home.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['courses'] = self.model.objects.all()
        return context


class CertificateTypeCreateView(CreateView):

    model = CertificateType
    fields = ['name']
    template_name = 'certificate_type/certificate-type-create.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, **self.kwargs)
        return context

    def form_valid(self, form: ModelForm):
        form.instance.course = get_object_or_404(Course, **self.kwargs)
        try:
            self.object = form.save()
        except IntegrityError:
            form.add_error(field='name', error=_('Такой тип сертификатов уже существует'))
            return super().form_invalid(form)
        return super().form_valid(form)


class ParseFileCreateView(CreateView):

    queryset = CertificateType.objects.all()
    model = ParseFile
    fields = ['file']
    template_name = 'parse_file/parse-file-create.html'
    context_object_name = 'certificate_type'

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(slug=self.kwargs.get('slug'), course__slug=self.kwargs.get('course_slug'))

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['certificate_type'] = get_object_or_404(self.get_queryset())
        return context

    def form_valid(self, form: ModelForm):
        form.instance.certificate_type = get_object_or_404(self.get_queryset())
        self.object = form.save()
        return super().form_valid(form)


class ParseSessionCreateView(CreateView):

    queryset = ParseFile.objects.all()
    model = ParseSession
    fields = ['start_with']
    template_name = 'parse_session/parse-session-create.html'
    context_object_name = 'parse_file'

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(id=self.kwargs.get('pk'), certificate_type__course__slug=self.kwargs.get('course_slug'),
                                    certificate_type__slug=self.kwargs.get('slug'))

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['parse_file'] = get_object_or_404(self.get_queryset())
        return context

    def form_valid(self, form: ModelForm):
        form.instance.parse_file = get_object_or_404(self.get_queryset())
        is_parse_session_exist = self.model.objects.filter(
            parse_file=form.instance.parse_file,
            start_with=form.cleaned_data.get('start_with'),
        ).exists()

        if is_parse_session_exist:
            form.add_error(field='start_with', error=_('Сертификаты с такими калибровочными параметрами уже существуют'))
            return super().form_invalid(form)
        self.object = form.save()
        return super().form_valid(form)


class ParseSessionDeleteView(DeleteView):

    model = ParseSession

    def get_success_url(self) -> str:
        return reverse('parse-session-create', kwargs={
            'course_slug': self.object.parse_file.certificate_type.course.slug,
            'slug': self.object.parse_file.certificate_type.slug,
            'pk': self.object.parse_file.pk,
        })


class CourseDeleteView(DeleteView):

    model = Course

    def get_success_url(self) -> str:
        return reverse('home')


class CertificateTypeDeleteView(DeleteView):

    queryset = CertificateType.objects.all()
    model = CertificateType

    def get_success_url(self) -> str:
        return reverse('certificate-type-create', kwargs={
            'slug': self.object.course.slug,
        })

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(slug=self.kwargs.get('slug'), course__slug=self.kwargs.get('course_slug'))


class ParseFileDeleteView(DeleteView):

    queryset = ParseFile.objects.all()
    model = ParseFile

    def get_success_url(self) -> str:
        return reverse('parse-file-create', kwargs={
            'course_slug': self.object.certificate_type.course.slug,
            'slug': self.object.certificate_type.slug,
        })

    def get_queryset(self) -> QuerySet:
        return self.queryset.filter(id=self.kwargs.get('pk'), certificate_type__course__slug=self.kwargs.get('course_slug'),
                                    certificate_type__slug=self.kwargs.get('slug'))
