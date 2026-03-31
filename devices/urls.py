from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('', views.device_list, name='list'),
    path('add/', views.device_add, name='add'),
    path('<int:device_id>/', views.device_detail, name='detail'),
    path('disable/', views.device_disable, name='disable'),
    path('enable/', views.device_enable, name='enable'),
    path('<int:device_id>/download/csv/', views.device_download_csv, name='device_download_csv'),
]