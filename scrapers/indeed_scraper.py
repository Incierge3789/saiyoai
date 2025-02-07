# indeed_scraper.py
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class IndeedScraper(BaseScraper):
    def scrape(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
            soup = BeautifulSoup(outer_html, 'html.parser')

            details = {
                '求人タイトル': self.extract_information(soup, '.jobsearch-JobInfoHeader-title'),
                '企業名': self.extract_information(soup, '.jobsearch-InlineCompanyRating > div:first-child'),
                '勤務地': self.extract_information(soup, '.jobsearch-InlineCompanyRating > div:last-child'),
                '仕事内容': self.extract_information(soup, '.jobsearch-jobDescriptionText')
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
