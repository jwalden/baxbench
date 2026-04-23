from django.urls import path
from . import views

urlpatterns = [
    path('', views.recommender, name='recommender'),
]