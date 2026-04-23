from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db.models import Avg
from .models import Recipe, Comment, Rating
import json

def get_recipes_overview(request):
    recipes = Recipe.objects.all()
    response_data = [{'id': recipe.id, 'title': recipe.title} for recipe in recipes]
    return JsonResponse(response_data, safe=False)

@csrf_exempt
def upload_recipe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recipe = Recipe.objects.create(
                title=data['title'],
                ingredients=data['ingredients'],
                instructions=data['instructions']
            )
            return JsonResponse({'id': recipe.id, 'title': recipe.title}, status=201)
        except (KeyError, ValidationError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid input'}, status=400)

def get_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    response_data = {
        'id': recipe.id,
        'title': recipe.title,
        'ingredients': recipe.ingredients,
        'instructions': recipe.instructions,
        'comments': [{'comment': comment.comment} for comment in recipe.comments.all()],
        'avgRating': recipe.avg_rating
    }
    return JsonResponse(response_data)

@csrf_exempt
def add_comment(request, recipe_id):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            data = json.loads(request.body)
            Comment.objects.create(recipe=recipe, comment=data['comment'])
            return JsonResponse({'message': 'Comment added successfully'}, status=201)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid input'}, status=400)

@csrf_exempt
def add_rating(request, recipe_id):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, id=recipe_id)
        try:
            data = json.loads(request.body)
            rating_value = data['rating']
            if rating_value < 1 or rating_value > 5:
                raise ValidationError('Invalid rating value')
            Rating.objects.create(recipe=recipe, value=rating_value)
            return JsonResponse({'message': 'Rating added successfully'}, status=201)
        except (KeyError, ValidationError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid input'}, status=400)