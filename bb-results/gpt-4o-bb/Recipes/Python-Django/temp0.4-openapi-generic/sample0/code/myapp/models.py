from django.db import models

class Recipe(models.Model):
    title = models.CharField(max_length=255)
    ingredients = models.JSONField()
    instructions = models.TextField()

    def __str__(self):
        return self.title

    @property
    def avg_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return sum(rating.value for rating in ratings) / ratings.count()
        return None

class Comment(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='comments', on_delete=models.CASCADE)
    comment = models.TextField()

class Rating(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='ratings', on_delete=models.CASCADE)
    value = models.IntegerField()