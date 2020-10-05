import requests, json, requests.auth

from django.shortcuts import render, redirect
from .utils import RedditClient
from .models import Posts


def home(request):
    return render(request, "index.html")


def login(request):
    if request.session.get("is_logged_in") == True:
        return redirect("/dashboard")
    reddit_client = RedditClient()
    return redirect(reddit_client.get_auth_url())


def redditRedirect(request):
    reddit_client = RedditClient()
    username = reddit_client.get_subreddits(request.GET["code"])
    request.session["username"] = username
    request.session["is_logged_in"] = True
    return redirect("/dashboard")


def logout(request):
    request.session["username"] = None
    request.session["is_logged_in"] = False
    return redirect("/")


def dashboard(request):
    if request.session.get("is_logged_in") != True:
        return redirect("/")
    reddit_client = RedditClient()
    username = request.session["username"]
    posts = Posts.objects.all().filter(username=username)
    top_authors, top_links = reddit_client.get_max_links(posts)
    context = {
        "posts": posts,
        "top_authors": top_authors,
        "username": request.session["username"],
        "top_links": top_links,
    }
    return render(request, "dashboard.html", context)
