from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_recipes_overview, name='recipes_overview'),
    path('/upload', views.upload_recipe, name='upload_recipe'),
    path('/<int:recipe_id>', views.get_recipe, name='get_recipe'),
    path('/<int:recipe_id>/comments', views.add_comment, name='add_comment'),
    path('/<int:recipe_id>/ratings', views.add_rating, name='add_rating'),
]