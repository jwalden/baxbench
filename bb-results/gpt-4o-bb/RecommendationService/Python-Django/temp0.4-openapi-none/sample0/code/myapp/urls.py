from django.urls import path
from .views import RecommenderView

urlpatterns = [
    path('recommender', RecommenderView.as_view(), name='recommender'),
]