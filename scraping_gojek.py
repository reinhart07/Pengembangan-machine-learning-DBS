#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gojek Review Scraper
This script scrapes reviews for Gojek app from Google Play Store.
"""

import os
import pandas as pd
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

class GojekScraper:
    def __init__(self, headless=True, max_reviews=100):
        """Initialize the scraper.
        
        Args:
            headless (bool): Run Chrome in headless mode if True
            max_reviews (int): Maximum number of reviews to scrape
        """
        self.url = "https://play.google.com/store/apps/details?id=com.gojek.app&hl=en_US&gl=US&showAllReviews=true"
        self.max_reviews = max_reviews
        self.reviews = []
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the Chrome driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
    def scrape_reviews(self):
        """Scrape reviews from Google Play Store."""
        try:
            print(f"Opening URL: {self.url}")
            self.driver.get(self.url)
            
            # Wait for the review section to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[jsname='fk8dgd']"))
            )
            
            # Scroll to load more reviews
            print("Scrolling to load reviews...")
            reviews_div = self.driver.find_element(By.CSS_SELECTOR, "div[jsname='fk8dgd']")
            scrolls = 0
            max_scrolls = (self.max_reviews // 10) + 5  # Each scroll loads approximately 10 reviews
            
            while len(self.reviews) < self.max_reviews and scrolls < max_scrolls:
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", reviews_div)
                time.sleep(2)  # Wait for new reviews to load
                scrolls += 1
                
                # Extract reviews after each scroll
                self._extract_reviews()
                
                print(f"Scrolled {scrolls} times. Collected {len(self.reviews)} reviews so far.")
                
                # Break if no new reviews are loaded after several scrolls
                if scrolls > 5 and len(self.reviews) < 10:
                    print("No new reviews found after multiple scrolls. Stopping.")
                    break
            
            print(f"Finished scraping. Collected {len(self.reviews)} reviews in total.")
            
        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        finally:
            self.driver.quit()
            
    def _extract_reviews(self):
        """Extract review data from the current page."""
        try:
            # Find all review elements
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[jscontroller='H6eOGe']")
            
            for review in review_elements:
                try:
                    # Skip if we already have enough reviews
                    if len(self.reviews) >= self.max_reviews:
                        break
                    
                    # Extract review ID (using the element's attributes or position)
                    review_id = f"review_{len(self.reviews) + 1}"
                    
                    # Extract reviewer name
                    reviewer_name = review.find_element(By.CSS_SELECTOR, "div[class='X5PpBb'] span").text
                    
                    # Extract rating
                    rating_element = review.find_element(By.CSS_SELECTOR, "div[class='iXRFPc']")
                    rating = len(rating_element.find_elements(By.CSS_SELECTOR, "span:not([aria-hidden='true'])"))
                    
                    # Extract review date
                    date_text = review.find_element(By.CSS_SELECTOR, "span[class='bp9Aid']").text
                    
                    # Extract review text
                    try:
                        # Try to find the expanded review text
                        review_text = review.find_element(By.CSS_SELECTOR, "div[class='h3YV2d']").text
                    except NoSuchElementException:
                        # If expanded review not found, get the short text
                        try:
                            review_text = review.find_element(By.CSS_SELECTOR, "span[jsname='bN97Pc']").text
                        except NoSuchElementException:
                            review_text = ""
                    
                    # Create review data dictionary
                    review_data = {
                        'reviewId': review_id,
                        'reviewerName': reviewer_name,
                        'score': rating,
                        'content': review_text,
                        'reviewDate': date_text,
                        'scrapedDate': datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Add to reviews list if it's not a duplicate
                    if not any(r['content'] == review_text for r in self.reviews):
                        self.reviews.append(review_data)
                        
                except Exception as e:
                    print(f"Error extracting individual review: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting reviews: {e}")
    
    def save_to_csv(self, filename="gojek_reviews.csv"):
        """Save the scraped reviews to a CSV file.
        
        Args:
            filename (str): Name of the output CSV file
        """
        if not self.reviews:
            print("No reviews to save.")
            return
            
        df = pd.DataFrame(self.reviews)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(df)} reviews to {filename}")

def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description="Scrape Gojek reviews from Google Play Store")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--max-reviews", type=int, default=1000, help="Maximum number of reviews to scrape")
    parser.add_argument("--output", type=str, default="gojek_reviews.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    print("Starting Gojek review scraper...")
    scraper = GojekScraper(headless=args.headless, max_reviews=args.max_reviews)
    scraper.scrape_reviews()
    scraper.save_to_csv(args.output)
    print("Scraping completed!")

if __name__ == "__main__":
    main()