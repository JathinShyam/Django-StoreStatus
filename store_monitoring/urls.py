from django.urls import path

from . import views

urlpatterns = [
    path("populate_store_status/", views.populate_store_status, name="populate_store_status"),
    path("populate_business_hours/", views.populate_business_hours, name="populate_business_hours"),
    path("populate_timezone/", views.populate_timezone, name="populate_timezone"),
    path('trigger_report/', views.trigger_report, name='trigger_report'),
    path('get_report/<str:report_id>/', views.get_report, name='get_report'),
]