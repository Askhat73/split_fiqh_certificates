from django.urls import path

from certificates.views import HomeView, CourseDetailView, \
    CertificateTypeDetailView, ParseFileDetailView, ParseSessionDeleteView, \
    CourseDeleteView, CertificateTypeDeleteView, ParseFileDeleteView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('courses/<slug:slug>/', CourseDetailView.as_view(), name='course-detail'),
    path('courses/<slug:course_slug>/type/<slug:slug>/', CertificateTypeDetailView.as_view(), name='certificate-type-detail'),
    path('courses/<slug:course_slug>/type/<slug:slug>/file/<int:pk>/', ParseFileDetailView.as_view(), name='parse-file-detail'),

    path('parse-session/<int:pk>/delete/', ParseSessionDeleteView.as_view(), name='parse-session-delete'),
    path('courses/<slug:slug>/delete/', CourseDeleteView.as_view(), name='course-delete'),
    path('courses/<slug:course_slug>/type/<slug:slug>/delete/', CertificateTypeDeleteView.as_view(), name='certificate-type-delete'),
    path('courses/<slug:course_slug>/type/<slug:slug>/file/<int:pk>/delete/', ParseFileDeleteView.as_view(), name='parse-file-delete'),
]
