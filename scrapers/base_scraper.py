# base_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import os
import time
import logging
import hashlib

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self):
        self.driver = self.initialize_driver()
    
    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        webdriver_path = os.getenv('PATH_TO_WEBDRIVER')
        chrome_binary_path = os.getenv('CHROME_BINARY_PATH')
        service = Service(webdriver_path)
        
        if chrome_binary_path:
            options.binary_location = chrome_binary_path

        options.add_argument('--headless')
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")

        return webdriver.Chrome(service=service, options=options)

    def quit_driver(self):
        self.driver.quit()

    def get_content_from_url(self, url):
        try:
            logger.debug(f"Attempting to scrape URL: {url}")
            self.driver.get(url)
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            cleaned_text = self.clean_text(text)
            logger.debug(f"Scraped and cleaned text: {cleaned_text[:100]}...")
            return cleaned_text
        except (WebDriverException, NoSuchElementException, TimeoutException) as e:
            logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
            raise

    def clean_text(self, text):
        return ' '.join(text.split())

    def generate_file_name_from_url(self, url):
        hash_object = hashlib.md5(url.encode())
        return hash_object.hexdigest() + '.html'

    def save_html_source(self, html_source, file_name, site_name):
        base_directory = '/path/to/scraping_results'  # Adjust the path as needed
        save_directory = os.path.join(base_directory, site_name)

        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        file_path = os.path.join(save_directory, file_name)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html_source)
        logger.info(f"HTML source saved to {file_path}")
