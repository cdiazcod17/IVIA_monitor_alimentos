from django.urls import path
from . import views

app_name = 'devices'
urlpatterns = [
    path('', views.device_list, name='list'),
    path('add/', views.device_add, name='add'),
    path('<int:device_id>/', views.device_detail, name='detail'),
]
