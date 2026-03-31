from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Recipe, Comment, Rating
import json

class RecipeListView(View):
    def get(self, request):
        recipes = Recipe.objects.all()
        response = "<html><body><h1>Recipes</h1><ul>"
        for recipe in recipes:
            response += f'<li><a href="/recipes/{recipe.id}">{recipe.title}</a></li>'
        response += "</ul></body></html>"
        return HttpResponse(response, content_type='text/html')

class RecipeDetailView(View):
    def get(self, request, recipeId):
        recipe = get_object_or_404(Recipe, pk=recipeId)
        response = f"<html><body><h1>{recipe.title}</h1><p>{recipe.instructions}</p><h2>Ingredients</h2><ul>"
        for ingredient in recipe.ingredients:
            response += f'<li>{ingredient}</li>'
        response += "</ul><h2>Comments</h2><ul>"
        for comment in recipe.comments.all():
            response += f'<li>{comment.comment}</li>'
        response += "</ul><h2>Average Rating</h2><p>"
        response += f'{recipe.avg_rating if recipe.avg_rating is not None else "No ratings yet"}'
        response += "</p></body></html>"
        return HttpResponse(response, content_type='text/html')

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
            return JsonResponse({
                'id': recipe.id,
                'title': recipe.title,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions,
                'comments': [],
                'avgRating': None
            }, status=201)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid input'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def add_comment(request, recipeId):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, pk=recipeId)
        try:
            data = json.loads(request.body)
            Comment.objects.create(recipe=recipe, comment=data['comment'])
            return HttpResponse(status=201)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid input'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def add_rating(request, recipeId):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, pk=recipeId)
        try:
            data = json.loads(request.body)
            rating_value = data['rating']
            if 1 <= rating_value <= 5:
                Rating.objects.create(recipe=recipe, value=rating_value)
                return HttpResponse(status=201)
            else:
                return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid input'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)