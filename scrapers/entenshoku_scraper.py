# entenshoku_scraper.py
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class EntenshokuScraper(BaseScraper):
    def scrape(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
            soup = BeautifulSoup(outer_html, 'html.parser')

            details = {
                'Catch': self.extract_information(soup, '#descCatchArea > div > div.catch'),
                'Copy': self.extract_information(soup, '#descCatchArea > div > div.copy'),
                '募集要項': self.extract_table_info(soup, 'body > div.pageSet > div:nth-child(3) > div.descArticleUnit.dataWork > div.contents > table > tbody > tr'),
                '会社概要': self.extract_table_info(soup, 'body > div.pageSet > div:nth-child(5) > div > div.contents > table > tbody > tr')
            }

            return details

        except Exception as e:
            logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
            raise
        finally:
            self.quit_driver()

    def extract_information(self, soup, selector):
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else 'Not Found'

    def extract_table_info(self, soup, selector):
        rows = soup.select(selector)
        info = {}
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            if th and td:
                info[th.get_text(strip=True)] = td.get_text(strip=True)
        return info
