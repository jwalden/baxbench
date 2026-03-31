from django.test import TestCase
from .models import Recipe, Comment, Rating

class RecipeModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Spaghetti Carbonara",
            ingredients=["Spaghetti", "Eggs", "Pancetta", "Parmesan Cheese"],
            instructions="Boil pasta. Cook pancetta. Mix eggs and cheese. Combine all."
        )

    def test_recipe_creation(self):
        self.assertEqual(self.recipe.title, "Spaghetti Carbonara")

class CommentModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Spaghetti Carbonara",
            ingredients=["Spaghetti", "Eggs", "Pancetta", "Parmesan Cheese"],
            instructions="Boil pasta. Cook pancetta. Mix eggs and cheese. Combine all."
        )
        self.comment = Comment.objects.create(recipe=self.recipe, comment="This recipe is amazing!")

    def test_comment_creation(self):
        self.assertEqual(self.comment.comment, "This recipe is amazing!")

class RatingModelTest(TestCase):
    def setUp(self):
        self.recipe = Recipe.objects.create(
            title="Spaghetti Carbonara",
            ingredients=["Spaghetti", "Eggs", "Pancetta", "Parmesan Cheese"],
            instructions="Boil pasta. Cook pancetta. Mix eggs and cheese. Combine all."
        )
        self.rating = Rating.objects.create(recipe=self.recipe, rating=5)

    def test_rating_creation(self):
        self.assertEqual(self.rating.rating, 5)