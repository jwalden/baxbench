from django.urls import path
from . import views

urlpatterns = [
    path('associate_card', views.associate_card, name='associate_card'),
    path('retrieve_cards', views.retrieve_cards, name='retrieve_cards'),
]