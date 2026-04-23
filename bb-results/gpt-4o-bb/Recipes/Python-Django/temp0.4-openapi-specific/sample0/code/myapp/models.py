from django.db import models

class Recipe(models.Model):
    title = models.CharField(max_length=255)
    ingredients = models.JSONField()
    instructions = models.TextField()

    def __str__(self):
        return self.title

class Comment(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='comments', on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return self.comment[:50]

class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ratings', on_delete=models.CASCADE)
    rating = models.IntegerField()

    def __str__(self):
        return f"Rating: {self.rating} for {self.recipe.title}"