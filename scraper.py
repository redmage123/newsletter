from typing import List, Tuple, Protocol, Callable
import threading
import snscrape.modules.twitter as sntwitter
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import concurrent.futures


class Scraper(Protocol):
    """
    Protocol class for the scraper classes.
    """

    async def scrape(self, *args) -> None:
        pass


class TwitterScraper:
    """
    A class used to scrape tweets from Twitter using snscrape and aiohttp.

    Attributes:
        data (List[Tuple[str, str, str, str, List[str]]]): A list of tuples containing scraped tweet data.
    """

    def __init__(self):
        self.data: List[Tuple[str, str, str, str, List[str]]] = []

    @staticmethod
    def extract_hashtags(content: str) -> List[str]:
        return [tag.strip('#') for tag in content.split() if tag.startswith('#')]

    def scrape(self, search_query: str, max_tweets: int) -> None:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(search_query).get_items()):
            if i >= max_tweets:
                break
            hashtags = self.extract_hashtags(tweet.content)
            self.data.append(("Twitter", tweet.user.username, tweet.id, tweet.content, tweet.date, hashtags))


class RedditScraper(Scraper):
    """
    A class used to scrape posts from Reddit using aiohttp and BeautifulSoup.

    Attributes:
        data (List[Tuple[str, str, str, str]]): A list of tuples containing scraped post data.
    """

    def __init__(self) -> None:
        self.data: List[Tuple[str, str, str, str]] = []

    async def scrape(self, subreddits: List[str], max_posts: int) -> None:
        """
        Scrapes the specified subreddits and stores the data in self.data.

        :param subreddits: A list of subreddit names to scrape.
        :param max_posts: The maximum number of posts to scrape from each subreddit.
        """
        pass  # Implement aiohttp-based Reddit scraping


class AIWeeklyScraper(Scraper):
    """
    A class used to scrape articles from AI Weekly using aiohttp and BeautifulSoup.

    Attributes:
        data (List[Tuple[str, str, str, str]]): A list of tuples containing scraped article data.
    """

    def __init__(self) -> None:
        self.data: List[Tuple[str, str, str, str]] = []

    async def scrape(self) -> None:
        """
        Scrapes articles from AI Weekly and stores the data in self.data.
        """
        pass  # Implement aiohttp-based AI Weekly scraping


class AITopicsScraper(Scraper):
    """
    A class used to scrape articles from AI Topics using aiohttp and BeautifulSoup.

    Attributes:
        data (List[Tuple[str, str, str, str]]): A list of tuples containing scraped article data.
    """

    def __init__(self) -> None:
        self.data: List[Tuple[str, str, str, str]] = []

    async def scrape(self) -> None:
        """
        Scrapes articles from AI Topics and stores the data in self.data.
        """
        pass  # Implement aiohttp-based AI Topics scraping

def run_in_thread(func: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.start()
        thread.join()

        if exception[0] is not None:
            raise exception[0]

        return result[0]

    return wrapper

def main() -> None:

    """
    Main function to run the scrapers concurrently using ThreadPoolExecutor.
    Scrapes data from Twitter, Reddit, AI Weekly, and AI Topics, combines the results,
    and saves them to a CSV file with a timestamp in the file name.
    """

    twitter_scraper = TwitterScraper()
    reddit_scraper = RedditScraper()
    aiweekly_scraper = AIWeeklyScraper()
    aitopics_scraper = AITopicsScraper()

    async def run_scrapers() -> None:
        non_async_twitter_scrape = run_in_thread(twitter_scraper.scrape)
        non_async_twitter_scrape('("artificial intelligence" OR "AI" OR "GPT" OR "GPT-4" OR "OpenAI")', 1000)
        reddit_scrape = await reddit_scraper.scrape(['ChatGPT', 'machinelearning', 'artificial', 'stablediffusion'], 10)
        aiweekly_scrape = await aiweekly_scraper.scrape()
        aitopics_scrape = await aitopics_scraper.scrape()

        # Combine scraped data
        combined_data = twitter_scraper.data + reddit_scraper.data + aiweekly_scraper.data + aitopics_scraper.data

        # Save to CSV
        df = pd.DataFrame(combined_data, columns=["Platform", "User", "ID", "Content", "Date", "URL/Hashtags"])
        df.to_csv(f'scrape_results_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv', index=False)

    asyncio.run(run_scrapers())


if __name__ == "__main__":
    main()
