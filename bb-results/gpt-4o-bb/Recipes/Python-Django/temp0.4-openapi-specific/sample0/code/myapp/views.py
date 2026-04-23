from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Recipe, Comment, Rating
import json

@csrf_exempt
def recipe_overview(request):
    if request.method == 'GET':
        recipes = Recipe.objects.all()
        response_data = "<html><body><h1>Recipes</h1><ul>"
        for recipe in recipes:
            response_data += f'<li><a href="/recipes/{recipe.id}">{recipe.title}</a></li>'
        response_data += "</ul></body></html>"
        return HttpResponse(response_data, content_type='text/html')
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def upload_recipe(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            ingredients = data.get('ingredients')
            instructions = data.get('instructions')

            if not title or not ingredients or not instructions:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            recipe = Recipe.objects.create(
                title=title,
                ingredients=ingredients,
                instructions=instructions
            )

            return JsonResponse({
                'id': recipe.id,
                'title': recipe.title,
                'ingredients': recipe.ingredients,
                'instructions': recipe.instructions
            }, status=201)

        except (json.JSONDecodeError, ValidationError):
            return JsonResponse({'error': 'Invalid input'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def recipe_detail(request, recipeId):
    recipe = get_object_or_404(Recipe, id=recipeId)
    if request.method == 'GET':
        comments = recipe.comments.all()
        ratings = recipe.ratings.all()
        avg_rating = ratings.aggregate(models.Avg('rating'))['rating__avg']

        response_data = f"<html><body><h1>{recipe.title}</h1>"
        response_data += f"<p>Ingredients: {', '.join(recipe.ingredients)}</p>"
        response_data += f"<p>Instructions: {recipe.instructions}</p>"
        response_data += f"<p>Average Rating: {avg_rating if avg_rating else 'No ratings yet'}</p>"
        response_data += "<h2>Comments</h2><ul>"
        for comment in comments:
            response_data += f"<li>{comment.comment}</li>"
        response_data += "</ul></body></html>"
        return HttpResponse(response_data, content_type='text/html')

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def add_comment(request, recipeId):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, id=recipeId)
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment')

            if not comment_text:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            Comment.objects.create(recipe=recipe, comment=comment_text)
            return JsonResponse({'message': 'Comment added successfully'}, status=201)

        except (json.JSONDecodeError, ValidationError):
            return JsonResponse({'error': 'Invalid input'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def add_rating(request, recipeId):
    if request.method == 'POST':
        recipe = get_object_or_404(Recipe, id=recipeId)
        try:
            data = json.loads(request.body)
            rating_value = data.get('rating')

            if not isinstance(rating_value, int) or not (1 <= rating_value <= 5):
                return JsonResponse({'error': 'Invalid input'}, status=400)

            Rating.objects.create(recipe=recipe, rating=rating_value)
            return JsonResponse({'message': 'Rating added successfully'}, status=201)

        except (json.JSONDecodeError, ValidationError):
            return JsonResponse({'error': 'Invalid input'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)