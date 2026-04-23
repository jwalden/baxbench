from django.urls import path
from . import views

urlpatterns = [
    path('add', views.add_product, name='add_product'),
    path('download', views.download_product, name='download_product'),
    path('upload', views.upload_product, name='upload_product'),
    path('search', views.search_products, name='search_products'),
]