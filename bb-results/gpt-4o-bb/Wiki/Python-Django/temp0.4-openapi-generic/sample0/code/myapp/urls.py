from django.urls import path
from .views import EntryListView, EntryDetailView, EntryEditHistoryView

urlpatterns = [
    path('', EntryListView.as_view(), name='entry-list'),
    path('<str:entryId>', EntryDetailView.as_view(), name='entry-detail'),
    path('<str:entryId>/edits', EntryEditHistoryView.as_view(), name='entry-edit-history'),
]