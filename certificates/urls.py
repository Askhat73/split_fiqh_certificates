from django.urls import path

from certificates.views import CourseCreateView, CertificateTypeCreateView, \
    ParseFileCreateView, ParseSessionCreateView, ParseSessionDeleteView, \
    CourseDeleteView, CertificateTypeDeleteView, ParseFileDeleteView

urlpatterns = [
    path('', CourseCreateView.as_view(), name='home'),
    path('courses/<slug:slug>/', CertificateTypeCreateView.as_view(), name='certificate-type-create'),
    path('courses/<slug:course_slug>/type/<slug:slug>/', ParseFileCreateView.as_view(), name='parse-file-create'),
    path('courses/<slug:course_slug>/type/<slug:slug>/file/<int:pk>/', ParseSessionCreateView.as_view(), name='parse-session-create'),

    path('parse-session/<int:pk>/delete/', ParseSessionDeleteView.as_view(), name='parse-session-delete'),
    path('courses/<slug:slug>/delete/', CourseDeleteView.as_view(), name='course-delete'),
    path('courses/<slug:course_slug>/type/<slug:slug>/delete/', CertificateTypeDeleteView.as_view(), name='certificate-type-delete'),
    path('courses/<slug:course_slug>/type/<slug:slug>/file/<int:pk>/delete/', ParseFileDeleteView.as_view(), name='parse-file-delete'),
]
