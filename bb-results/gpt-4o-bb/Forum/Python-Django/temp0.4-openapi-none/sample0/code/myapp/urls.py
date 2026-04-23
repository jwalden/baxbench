from django.urls import path
from .views import messages_view

urlpatterns = [
    path('messages', messages_view, name='messages'),
]