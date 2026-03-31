from django.urls import path
from . import views

urlpatterns = [
    path('decideUnsubscribe', views.decide_unsubscribe, name='decide_unsubscribe'),
]