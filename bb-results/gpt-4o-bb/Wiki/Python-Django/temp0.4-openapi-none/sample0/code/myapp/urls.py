from django.urls import path
from . import views

urlpatterns = [
    path('entries', views.entries, name='entries'),
    path('entries/<int:entry_id>', views.entry_detail, name='entry_detail'),
    path('entries/<int:entry_id>/edits', views.entry_edits, name='entry_edits'),
]