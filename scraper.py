#!c:/User/bbrel/newsletter/.venv/Scripts/Python.exe 
"""
This module contains two classes, TwitterScraper and RedditScraper, for scraping content from Twitter and Reddit
respectively using snscrape and BeautifulSoup.
"""

import snscrape.modules.twitter as sntwitter
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from typing import List, Tuple, Union


class TwitterScraper:
    """
    A class used to scrape tweets from Twitter using snscrape.

    Attributes:
        data (List[Tuple[str, str, str, str, List[str]]]): A list of tuples containing scraped tweet data.
    """

    def __init__(self):
        self.data: List[Tuple[str, str, str, str, List[str]]] = []

    @staticmethod
    def extract_hashtags(content: str) -> List[str]:
        """
        Extracts hashtags from the given content.

        :param content: A string containing the content.
        :return: A list of hashtags found in the content.
        """
        return [tag.strip('#') for tag in content.split() if tag.startswith('#')]

    def scrape(self, search_query: str, max_tweets: int) -> None:
        """
        Scrapes tweets using the given search query and stores the data in self.data.

        :param search_query:
        :param max_tweets: The maximum number of tweets to scrape.
        """
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(search_query).get_items()):
            if i > max_tweets:
                break
            hashtags = self.extract_hashtags(tweet.content)
            self.data.append(("Twitter", tweet.user.username, tweet.id, tweet.content, tweet.date, hashtags))


class RedditScraper:
    """
        A class used to scrape posts from Reddit using requests and BeautifulSoup.
        iAttributes:
        data (List[Tuple[str, str, str, str]]): A list of tuples containing scraped post data.
    """

    def __init__(self):
        self.data: List[Tuple[str, str, str, str]] = []

    @staticmethod
    def scrape_subreddit(subreddit: str, max_posts: int) -> List[Tuple[str, str, str]]:
        """
        Scrapes the specified subreddit and returns the data as a list of tuples.

        :param subreddit: The name of the subreddit to scrape.
        :param max_posts: The maximum number of posts to scrape.
        :return: A list of tuples containing post data (title, URL, date).
        """
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f'https://www.reddit.com/r/{subreddit}/new/.json'
        response = requests.get(url, headers=headers)
        json_data = response.json()
        post_data = []
        for post in json_data['data']['children']:
            title = post['data']['title']
            url = post['data']['url']
            date = datetime.datetime.utcfromtimestamp(post['data']['created_utc']).strftime('%Y-%m-%d %H:%M:%S')
            post_data.append((title, url, date))

        return post_data[:max_posts]

    def scrape(self, subreddits: List[str], max_posts: int) -> None:
        """
        Scrapes the specified subreddits and stores the data in self.data.

        :param subreddits: A list of subreddit names to scrape.
        :param max_posts: The maximum number of posts to scrape from each subreddit.
        """
        for subreddit in subreddits:
            posts = self.scrape_subreddit(subreddit, max_posts)
            for title, url, date in posts:
                self.data.append(("Reddit", subreddit, "", title, date, url))
 
def main():
# Twitter scraping
    twitter_scraper = TwitterScraper()
    twitter_scraper.scrape('("artificial intelligence" OR "AI" OR "GPT" OR "GPT-4" OR "OpenAI" OR "machine learning") lang:en', 10)
# Reddit scraping
    reddit_scraper = RedditScraper()
    reddit_scraper.scrape(['ChatGPT', 'machinelearning', 'artificial', 'stablediffusion', 'deepdream', 'futurology', 'singularity'], 5)

# Combine results and create a DataFrame
combined_data = twitter_scraper.data + reddit_scraper.data
df = pd.DataFrame(combined_data, columns=["Platform", "User", "ID", "Content", "Date", "URL/Hashtags"])

# Display the DataFrame
print(df)