import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
import random
from typing import List, Dict
import time
import platform
import os
from datetime import datetime
class G2Scraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self):
        """Async initialization method"""
        self.playwright = await async_playwright().start()
        
        chromium = self.playwright.chromium
        self.browser = await chromium.connect_over_cdp('wss://connect.browserbase.com?apiKey='+ os.environ["BROWSERBASE_API_KEY"])
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

    async def get_product_reviews(self, product_url: str, num_pages: int = 1, product_name: str = "example-product") -> List[Dict]:
        reviews = []
        
        # First visit the main product page
        print("Visiting main page...")
        await self.page.goto(product_url)
        await asyncio.sleep(2)  # Short wait for page load
        
        for page in range(1, num_pages + 1):
            print(f"Processing page {page}...")
            
            # Add timestamp to URL
            timestamp = int(time.time() * 1000)
            url = f"{product_url}?page={page}"
            
            await asyncio.sleep(5)  # Short delay between pages
            
            # Navigate to the page and wait for content to load
            await self.page.goto(url)
            

            
            # Get the page content and parse with BeautifulSoup
            content = await self.page.content()
            print("found content")
            soup = BeautifulSoup(content, 'html.parser')
            review_elements = soup.find_all("div", class_="paper paper--white paper--box mb-2 position-relative border-bottom")
            
            if not review_elements:
                print(f"No reviews found on page {page}")
                return reviews
            
            for review in review_elements:
                review_data = {
                    'text': self._extract_text(review),
                    'rating': self._extract_rating(review),
                    'date': self._extract_date(review),
                    'reviewer': self._extract_reviewer(review)
                }
                print(review_data)
                reviews.append(review_data)
        
        return reviews


    def _extract_text(self, review_element) -> str:
        review_body = review_element.find("div", attrs={"itemprop": "reviewBody"}).text
        return review_body

    def _extract_rating(self, review_element) -> int:
        rating_container = review_element.find("div", class_="f-1 d-f ai-c mb-half-small-only")
        rating_div = rating_container.find("div")

        rating_class = rating_div.get("class")

        stars_string = rating_class[-1]
        stars_large_number = float(stars_string.split("-")[-1])
        stars_clean_number = stars_large_number/2
        return stars_clean_number
    def _extract_date(self, review_element) -> str:
        review_date = review_element.find("time")
        date = review_date.get("datetime")
        return date

    def _extract_reviewer(self, review_element) -> str:
        name_present = review_element.find("a", class_="link--header-color")
        name = name_present.text if name_present else "anonymous"
        return name

async def run(product_name: str):
    scraper = G2Scraper()
    try:
        print("Initializing scraper...")
        await scraper.initialize()
        print("Connected to Chrome successfully!")
        
        # Add initial delay before starting
        await asyncio.sleep(random.uniform(5, 10))
        
        product_url = f"https://www.g2.com/products/{product_name}/reviews"
        reviews = await scraper.get_product_reviews(product_url, num_pages=100, product_name=product_name)
        
        if reviews:
            df = pd.DataFrame(reviews)
            filename = f'g2_reviews_{product_name}_{datetime.now().strftime("%Y-%m-%d")}.csv'
            df.to_csv(filename, index=False)
            print(f"Successfully saved {len(reviews)} reviews to {filename}")
        else:
            print("No reviews were collected")

        return filename
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        await scraper.browser.close()
        await scraper.playwright.stop()
        await scraper.context.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <company_name>")
        sys.exit(1)
    
    asyncio.run(run(sys.argv[1]))