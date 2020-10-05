import requests, requests.auth
import re

from collections import OrderedDict
from django.contrib.auth.models import User
from .models import Posts

from .constants import (
    auth_url,
    redirect_url,
    token_url,
    client_id,
    client_secret,
    url_regex,
    subreddits_url,
    username_url,
)
from urllib.parse import urlparse


class RedditClient:
    def __init__(self):
        self.client_auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        self.max_links = None

    def get_access_token(self, code):
        post_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_url,
        }

        headers = {
            "User-agent": "your bot 0.1",
        }

        response = requests.post(
            token_url,
            data=post_data,
            auth=self.client_auth,
            headers=headers,
        )

        return response.json()["access_token"]

    def get_auth_url(self):
        return auth_url

    def get_subreddits(self, code):
        access_token = self.get_access_token(code)
        username = self.get_username(access_token)
        posts = Posts.objects.all().filter(username=username)
        if len(posts) > 0:
            return username
        headers = {
            "Authorization": "bearer " + access_token,
            "User-agent": "your bot 0.1",
        }
        response = requests.get(subreddits_url, headers=headers)

        posts_list = []
        subreddits = response.json()["data"]["children"]

        for subreddit in subreddits:
            subreddit_name = subreddit["data"]["display_name"]
            post_url = "https://reddit.com/r/" + subreddit_name + "/hot.json?limit=100"
            response = requests.get(post_url, headers=headers)
            posts = response.json()["data"]["children"]

            for post in posts:
                text = post["data"]["selftext"]
                author = post["data"]["author"]
                title = post["data"]["title"]
                link = post["data"]["url"]
                links = self.get_links(text)
                if links is not None and len(links) > 0:
                    posts_list.append(
                        {
                            "text": text,
                            "author": author,
                            "title": title,
                            "link": link,
                            "subreddit": subreddit_name,
                        }
                    )

        self.ingest_data(posts_list, username)
        return username

    def get_links(self, text):
        urls = re.findall(url_regex, text)
        return urls

    def ingest_data(self, posts_list, username):
        for post in posts_list:
            Posts.objects.create(
                username=username,
                author=post["author"],
                text=post["text"],
                title=post["title"],
                link=post["link"],
                subreddit=post["subreddit"],
            )

    def get_username(self, access_token):
        headers = {
            "Authorization": "bearer " + access_token,
            "User-agent": "your bot 0.1",
        }
        response = requests.get(username_url, headers=headers)
        return response.json()["name"]

    def get_max_links(self, posts):
        authors = {}
        for post in posts:
            links = self.get_links(post.text)
            if post.author in authors.keys():
                authors[post.author]["links"] += links
                authors[post.author]["length"] = len(authors[post.author]["links"])
            else:
                authors[post.author] = {}
                authors[post.author]["links"] = links
                authors[post.author]["length"] = len(authors[post.author]["links"])

        top_authors = self.find_top_authors(authors)
        top_domains = self.get_top_domains(authors)
        return top_authors, top_domains

    def extract_domain(self, url, remove_http=True):
        uri = urlparse(url)
        if uri.path == url:
            return url
        if remove_http:
            domain_name = f"{uri.netloc}"
        else:
            domain_name = f"{uri.netloc}://{uri.netloc}"
        if domain_name.find("www.") > -1:
            domain_name = domain_name[domain_name.find("www.") + 4 :]
        return domain_name

    def find_top_authors(self, authors, count=5):
        sortedauthors = sorted(authors.items(), key=lambda x: int(x[1]["length"]))
        sortedauthors.reverse()
        topauthors = []
        for i in range(min(count, len(sortedauthors))):
            topauthors.append((sortedauthors[i][0], int(sortedauthors[i][1]["length"])))
        return topauthors

    def get_top_domains(self, authors, count=5):
        domainfrequency = dict()
        for i in authors.values():
            for j in i["links"]:
                domain = self.extract_domain(j)
                if domain in domainfrequency:
                    domainfrequency[domain] += 1
                elif len(domain) > 0:
                    domainfrequency[domain] = 1
        sorteddomains = sorted(domainfrequency.items(), key=lambda x: -int(x[1]))
        reducedlist = []
        for i in range(min(len(sorteddomains), count)):
            reducedlist.append(sorteddomains[i])
        return reducedlist