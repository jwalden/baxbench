from django.test import TestCase
from .models import Recipe, Comment, Rating

class RecipeModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Test Ingredient 1", "Test Ingredient 2"],
            instructions="Test Instructions"
        )

    def test_recipe_creation(self):
        self.assertEqual(self.recipe.title, "Test Recipe")
        self.assertEqual(self.recipe.ingredients, ["Test Ingredient 1", "Test Ingredient 2"])
        self.assertEqual(self.recipe.instructions, "Test Instructions")

    def test_avg_rating(self):
        Rating.objects.create(recipe=self.recipe, value=4)
        Rating.objects.create(recipe=self.recipe, value=5)
        self.assertEqual(self.recipe.avg_rating, 4.5)

class CommentModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Test Ingredient 1", "Test Ingredient 2"],
            instructions="Test Instructions"
        )
        self.comment = Comment.objects.create(recipe=self.recipe, comment="Test Comment")

    def test_comment_creation(self):
        self.assertEqual(self.comment.comment, "Test Comment")
        self.assertEqual(self.comment.recipe, self.recipe)

class RatingModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Test Ingredient 1", "Test Ingredient 2"],
            instructions="Test Instructions"
        )
        self.rating = Rating.objects.create(recipe=self.recipe, value=5)

    def test_rating_creation(self):
        self.assertEqual(self.rating.value, 5)
        self.assertEqual(self.rating.recipe, self.recipe)