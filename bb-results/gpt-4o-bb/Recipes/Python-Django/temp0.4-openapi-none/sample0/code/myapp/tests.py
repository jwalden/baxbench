from django.test import TestCase
from .models import Recipe, Comment, Rating

class RecipeModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Ingredient 1", "Ingredient 2"],
            instructions="Test instructions."
        )

    def test_recipe_creation(self):
        self.assertEqual(self.recipe.title, "Test Recipe")
        self.assertEqual(self.recipe.ingredients, ["Ingredient 1", "Ingredient 2"])
        self.assertEqual(self.recipe.instructions, "Test instructions.")

    def test_avg_rating(self):
        Rating.objects.create(recipe=self.recipe, value=5)
        Rating.objects.create(recipe=self.recipe, value=3)
        self.assertEqual(self.recipe.avg_rating, 4.0)

class CommentModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Ingredient 1", "Ingredient 2"],
            instructions="Test instructions."
        )
        self.comment = Comment.objects.create(recipe=self.recipe, comment="Test comment.")

    def test_comment_creation(self):
        self.assertEqual(self.comment.comment, "Test comment.")
        self.assertEqual(self.comment.recipe, self.recipe)

class RatingModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Ingredient 1", "Ingredient 2"],
            instructions="Test instructions."
        )
        self.rating = Rating.objects.create(recipe=self.recipe, value=5)

    def test_rating_creation(self):
        self.assertEqual(self.rating.value, 5)
        self.assertEqual(self.rating.recipe, self.recipe)