from django.db import models


class Posts(models.Model):
    username = models.CharField(max_length=100, blank=False)
    author = models.CharField(max_length=100, blank=False)
    text = models.TextField(blank=False)
    title = models.TextField(blank=False)
    link = models.URLField(max_length=400, blank=False)
    subreddit = models.URLField(max_length=400, blank=True)

    def __str__(self):
        return self.author + " " + self.title
