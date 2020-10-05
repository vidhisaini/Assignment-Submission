from django.urls import path, include
from .views import login, home, redditRedirect, logout, dashboard

urlpatterns = [
    path("", home),
    path("login", login),
    path("redirect", redditRedirect),
    path("logout", logout),
    path("dashboard", dashboard),
]
