from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Donor
    path("donate/new/", views.donate_new, name="donate_new"),
    path("requests/new/", views.request_new, name="request_new"),
    path("requests/mine/", views.request_mine, name="request_mine"),
    # Doctor
    path("doctor/requests/", views.doctor_requests, name="doctor_requests"),
    path("doctor/requests/<int:pk>/approve/", views.request_approve, name="request_approve"),
    path("doctor/requests/<int:pk>/reject/", views.request_reject, name="request_reject"),
    path("doctor/stock/", views.stock_view, name="stock_view"),
    path("doctor/stock/export-pdf/", views.stock_pdf, name="stock_pdf"),
    # Student
    path("student/stock/", views.student_stock, name="student_stock"),
    path("student/stock/export-pdf/", views.student_stock_pdf, name="student_stock_pdf"),
    path("doctor/stock/export-pdf/", views.stock_pdf, name="stock_pdf"),
]
