from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('', views.device_list, name='list'),
    path('add/', views.device_add, name='add'),
    path('latest/', views.device_list_latest_json, name='list_latest_json'),
    path('<int:device_id>/', views.device_detail, name='detail'),
    path('<int:device_id>/json/', views.device_readings_json, name='detail_json'),
    path('disable/', views.device_disable, name='disable'),
    path('enable/', views.device_enable, name='enable'),
    path('<int:device_id>/download/csv/', views.device_download_csv, name='device_download_csv'),
    path('api/set-global-frequency/', views.set_global_frequency, name='set_global_frequency'),
    path('api/set-device-frequency/', views.set_device_frequency, name='set_device_frequency'),
    path('api/command-status/', views.get_command_status, name='get_command_status'),
    path('api/device-config/', views.get_device_config, name='get_device_config'),
]