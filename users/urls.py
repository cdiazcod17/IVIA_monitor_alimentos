from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signin/', views.SigninView.as_view(), name='signin'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signout/', views.signout, name='signout'),
]
