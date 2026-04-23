from django.urls import path
from . import views

urlpatterns = [
    path('merchants/register', views.register_merchant, name='register_merchant'),
    path('merchants/login', views.login_merchant, name='login_merchant'),
    path('merchants/upload-wares', views.upload_wares, name='upload_wares'),
    path('wares', views.list_wares, name='list_wares'),
]