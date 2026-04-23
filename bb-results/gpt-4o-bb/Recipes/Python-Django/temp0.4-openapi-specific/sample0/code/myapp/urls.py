from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipe_overview, name='recipe_overview'),
    path('/upload', views.upload_recipe, name='upload_recipe'),
    path('/<str:recipeId>', views.recipe_detail, name='recipe_detail'),
    path('/<str:recipeId>/comments', views.add_comment, name='add_comment'),
    path('/<str:recipeId>/ratings', views.add_rating, name='add_rating'),
]