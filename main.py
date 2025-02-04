import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
import random
from typing import List, Dict
import time
import platform
import os

class G2Scraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self):
        """Async initialization method"""
        self.playwright = await async_playwright().start()
        
        # Mac-specific Chrome user data directory
        user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            args=['--start-maximized'],
            ignore_default_args=['--enable-automation']
        )
        
        # Get existing page or create new one
        pages = self.browser.pages
        self.page = pages[0] if pages else await self.browser.new_page()
        self.context = self.browser  # For persistent contexts, browser is the context
        
        # Add stealth plugins
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
        """)

    async def get_product_reviews(self, product_url: str, num_pages: int = 1, product_name: str = "example-product") -> List[Dict]:
        reviews = []
        
        # First visit the main product page with much longer initial wait
        print("Visiting main page...")
        await self.page.goto(product_url, wait_until="networkidle")
        await asyncio.sleep(random.uniform(10, 15))  # Much longer initial wait
        
        # Simulate human-like initial page interaction
        await self._simulate_human_reading()
        
        for page in range(1, num_pages + 1):
            print(f"Processing page {page}...")
            # Add random query parameters to look more natural
            timestamp = int(time.time() * 1000)
            url = f"{product_url}?page={page}&_t={timestamp}"
            
            # Much longer delay between pages
            await asyncio.sleep(random.uniform(20, 30))
            
            # Navigate to the page and wait for content to load
            await self.page.goto(url, wait_until="networkidle")
            await asyncio.sleep(random.uniform(5, 8))
            
            # Simulate reading and interaction before scrolling
            await self._simulate_human_reading()
            
            try:
                # Wait for reviews with longer timeout
                await self.page.wait_for_selector(".paper--box", state="visible", timeout=20000)
            except Exception:
                print(f"No reviews found on page {page}, might be blocked or no content")
                break
            
            # Get the page content and parse with BeautifulSoup
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            review_elements = soup.find_all("div", class_="paper paper--white paper--box mb-2 position-relative border-bottom")
            
            for review in review_elements:
                review_data = {
                    'text': self._extract_text(review),
                    'rating': self._extract_rating(review),
                    'date': self._extract_date(review),
                    'reviewer': self._extract_reviewer(review)
                }
                reviews.append(review_data)
        
        return reviews

    async def _simulate_human_reading(self):
        """Simulate human-like reading and interaction behavior"""
        # Random initial pause as if reading
        await asyncio.sleep(random.uniform(5, 10))
        
        # Simulate mouse movement as if reading
        for _ in range(random.randint(3, 6)):
            # Move mouse in a more natural pattern
            start_x = random.randint(100, 800)
            start_y = random.randint(100, 600)
            
            # Move to several points to simulate natural cursor movement
            points = [(start_x + random.randint(-100, 100), start_y + random.randint(-50, 50)) 
                     for _ in range(3)]
            
            for x, y in points:
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.5, 2))
        
        # Scroll slowly and naturally
        page_height = await self.page.evaluate('() => document.documentElement.scrollHeight')
        current_position = 0
        
        while current_position < page_height:
            # Smaller, more natural scroll amounts
            scroll_amount = random.randint(100, 200)
            current_position += scroll_amount
            await self.page.evaluate(f'window.scrollTo({{top: {current_position}, behavior: "smooth"}})')
            
            # Pause between scrolls as if reading
            await asyncio.sleep(random.uniform(2, 4))
            
            # Occasionally move mouse while scrolling
            if random.random() < 0.3:
                await self.page.mouse.move(
                    random.randint(100, 800),
                    random.randint(current_position - 100, current_position + 100)
                )
                await asyncio.sleep(random.uniform(1, 2))
        
        # Sometimes click on non-interactive elements as if selecting text
        if random.random() < 0.3:
            await self.page.mouse.click(
                random.randint(100, 800),
                random.randint(100, 600)
            )

    async def cleanup(self):
        """Clean up resources"""
        try:
            # Only close context if it exists and isn't already closed
            if self.context and not self.context.is_closed():
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup warning: {e}")
            # Don't raise the error since we're in cleanup

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
        reviews = await scraper.get_product_reviews(product_url, num_pages=2, product_name=product_name)
        
        if reviews:
            df = pd.DataFrame(reviews)
            df.to_csv('g2_reviews.csv', index=False)
            print(f"Successfully saved {len(reviews)} reviews to g2_reviews.csv")
        else:
            print("No reviews were collected")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        await scraper.cleanup()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <company_name>")
        sys.exit(1)
    
    asyncio.run(run(sys.argv[1]))