from django.urls import path
from . import views

urlpatterns = [
    path('recipes', views.RecipeListView.as_view(), name='recipe-list'),
    path('recipes/upload', views.upload_recipe, name='upload-recipe'),
    path('recipes/<int:recipeId>', views.RecipeDetailView.as_view(), name='recipe-detail'),
    path('recipes/<int:recipeId>/comments', views.add_comment, name='add-comment'),
    path('recipes/<int:recipeId>/ratings', views.add_rating, name='add-rating'),
]