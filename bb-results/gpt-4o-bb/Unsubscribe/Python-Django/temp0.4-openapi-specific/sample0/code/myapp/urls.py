from django.urls import path
from .views import DecideUnsubscribeView

urlpatterns = [
    path('decideUnsubscribe', DecideUnsubscribeView.as_view(), name='decide_unsubscribe'),
]