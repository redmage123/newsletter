import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Tuple, Optional, Iterable
import threading
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
import snscrape.modules.twitter as sntwitter
from tqdm.asyncio import tqdm
from queue import Queue
import itertools

class Scraper:

    """
    Base scraper class to be inherited by other scraper classes.
    """

    def __init__(self):
        self.data: List[Tuple[str, str, str, str, str, str]] = []

    def run_tqdm(self, iterable: Iterable, desc: Optional[str] = None, mininterval: float = 0.1) -> Iterable:

        """
            Wraps an iterable with a tqdm progress bar.

            Args:
                iterable (Iterable): The iterable to be wrapped with a tqdm progress bar.
                desc (Optional[str]): A description for the progress bar. Defaults to None.
                mininterval (float): The minimum interval in seconds between updates. This ensures more frequent updates
                             of the progress bar, even when the number of items in the iterable is small.
                             Defaults to 0.1.

            Returns:
                Iterable: The wrapped iterable with a tqdm progress bar.
        """

        bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        with tqdm(iterable,  bar_format=bar_format) as pbar:
            for item in pbar:
                yield item


    async def scrape(self) -> None:

        """
        Scraping method to be implemented by subclasses.
        """
        pass

class TwitterScraper(Scraper):
    """
    A class to scrape tweets using snscrape.
    """

    def __init__(self):
        super().__init__()
        self.thread  = None
        self.data = []

    def start_scrape(self, query: str, max_results: int) -> None:
        """
        Starts the scraping process in a separate thread.

        Args:
            query (str): The query to use for searching tweets.
            max_results (int): The maximum number of tweets to scrape.
        """
        self.thread = threading.Thread(target=self.scrape, args=(query, max_results))
        self.thread.start()

    def scrape(self, query: str, max_results: int) -> None:
        """
        Scrapes tweets using snscrape with a given query and maximum number of results.

        Args:
            query (str): The query to use for searching tweets.
            max_results (int): The maximum number of tweets to scrape.
        """
        scraped_tweets = []
        tweet_iterator = sntwitter.TwitterSearchScraper(query).get_items()

        for i, tweet in enumerate(self.run_tqdm(tweet_iterator)):
            if i >= max_results:
                break
            scraped_tweets.append(tweet)

        for tweet in scraped_tweets:
            # hashtags = [hashtag.tag for hashtag in tweet.entities['hashtags']]
            hashtags = tweet.hashtags
            self.data.append(("Twitter", tweet.user.username, tweet.id, tweet.content, tweet.date, hashtags))

    def join(self) -> None:
        """
        Waits for the scrape thread to finish.
        """
        if self.thread is not None:
            self.thread.join()

class RedditScraper(Scraper):
    """
    A class to scrape Reddit posts using aiohttp.
    """
    async def scrape(self, subreddits: List[str], max_posts: int) -> None:
        """
        Scrapes Reddit posts using aiohttp from the given subreddits with a maximum number of posts per subreddit.

        Args:
            subreddits (List[str]): A list of subreddits to scrape.
            max_posts (int): The maximum number of posts to scrape per subreddit.
        """
        async with aiohttp.ClientSession() as session:
            for subreddit in self.run_tqdm(subreddits,desc="subreddits"):
                url = f"https://www.reddit.com/r/{subreddit}/new.json"
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    json_data = await response.json()
                    posts = json_data["data"]["children"]
                    for i, post in enumerate(posts):
                        if i >= max_posts:
                            break
                        post_data = post["data"]
                        self.data.append(("Reddit", post_data["author"], post_data["id"], post_data["title"], post_data["created_utc"], post_data["url"]))

class AIWeeklyScraper(Scraper):
    """
    A class to scrape AI Weekly articles using aiohttp and BeautifulSoup.
    """
    async def scrape(self) -> None:
        """
        Scrapes AI Weekly articles using aiohttp and BeautifulSoup.
        """
        async with aiohttp.ClientSession() as session:
            url = "https://aiweekly.co/"
            async with session.get(url) as response:
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                articles = soup.find_all('article')
                for article in self.run_tqdm(articles,desc = "AIWeekly Scraper"):
                    title = article.h2.get_text(strip=True)
                    url_element = article.find('a', class_='issue-link')
                    url = url_element['href'] if url_element is not None else None
                    if url is not None:
                        self.data.append(("AI Weekly", "AIWeekly", "", title, "", url))

class AITopicsScraper(Scraper):

    """
    Scraper for the AI Topics website.
    """

    def __init__(self) -> None:
        self.data: List[Tuple[Any]] = []

    async def scrape(self) -> List[Tuple[Any]]:

        """
        Scrapes AI-related articles from the AI Topics website using the aiohttp client and Beautiful Soup.

        Returns:
            List[Tuple[Any]]: A list of tuples containing the scraped data.
        """

        async with aiohttp.ClientSession() as session:
           url = "https://aitopics.org/search"
           async with session.get(url) as response:
               html_content = await response.text()
               soup = BeautifulSoup(html_content, 'html.parser')
               articles = soup.find_all('div', class_='ai1ec-event-container')
               for article in self.run_tqdm(articles,desc="AITopics Scraper"):
                   title_element = article.find('span', class_='ai1ec-event-title')
                   title = title_element.get_text(strip=True) if title_element is not None else None
                   url_element = article.find('a', class_='ai1ec-load-event')
                   url = url_element['href'] if url_element is not None else None
                   if title is not None and url is not None:
                       self.data.append(("AI Topics", "AITopics", "", title, "", url))

async def run_scrapers(executor: ThreadPoolExecutor) -> None:

    """
    Run the scrapers concurrently using ThreadPoolExecutor and collect the scraped data.

    The TwitterScraper is run in a separate thread using the ThreadPoolExecutor, while the other scrapers
    are run asynchronously using asyncio.

    Args:
        executor (ThreadPoolExecutor): The executor to run the TwitterScraper concurrently.
    """

    combined_data = Queue()
    reddit_scraper = RedditScraper()
    aiweekly_scraper = AIWeeklyScraper()
    aitopics_scraper = AITopicsScraper()


    loop = asyncio.get_running_loop()
    await reddit_scraper.scrape(['ChatGPT', 'machinelearning', 'artificial', 'stablediffusion'], 10)
    await aiweekly_scraper.scrape()
    await aitopics_scraper.scrape()

    combined_data.put(reddit_scraper.data + aiweekly_scraper.data + aitopics_scraper.data)


def main() -> None:
    """
    Main function to run the scrapers concurrently using ThreadPoolExecutor.
    Scrapes data from Twitter, Reddit, AI Weekly, and AI Topics, combines the results,
    and saves them to a CSV file with a timestamp in the file name.
    """

    combined_data = Queue()
    twitter_scraper = TwitterScraper()
    twitter_query = '("artificial intelligence" OR "AI" OR "GPT" OR "GPT-4" OR "OpenAI")'
    num_twitter_results = 1000

    '''
    Because the snscrape library used to scrape Twitter doesn't support
    Python asyncio, I have to put it in a separate thread
    '''

    twitter_scraper.start_scrape(twitter_query, num_twitter_results)

    # All th rest ofr the scrapers use asyncio

    with ThreadPoolExecutor() as executor:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_scrapers(executor))
        finally:
            loop.close()

    twitter_scraper.join()  # Wait for the thread to finish
    combined_data.put(twitter_scraper.data)

    '''
        In order to put the scraped data into a dataframe, I have to extract
        queue elements one by one and put them into a list that can be passed
        to the pd.DataFrame initialixer

        Additionally, the data is coming in as a list of lists.  We use
        the itertools.chain_from_iterable to flatten the list.
    '''

    df_data = [combined_data.get() for _ in range(combined_data.qsize())]
    df_flattened_data =  list(itertools.chain.from_iterable(df_data))

    df = pd.DataFrame(df_flattened_data, columns=["Platform", "User", "ID", "Content", "Date", "URL/Hashtags"])
    df.to_csv(f'scraper_output/scrape_results_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv', index=False)

if __name__ == "__main__":
    main()
