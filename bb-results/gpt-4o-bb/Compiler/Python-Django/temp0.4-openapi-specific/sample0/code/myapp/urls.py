from django.urls import path
from .views import CompileView

urlpatterns = [
    path('compile', CompileView.as_view(), name='compile'),
]