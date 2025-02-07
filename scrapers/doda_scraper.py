# doda_scraper.py
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class DodaScraper(BaseScraper):
    def scrape(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
            soup = BeautifulSoup(outer_html, 'html.parser')

            details = {
                '企業情報': self.extract_information(soup, '企業情報'),
                '仕事内容': self.extract_information(soup, '仕事内容'),
                '対象となる方': self.extract_information(soup, '対象となる方'),
                '勤務地': self.extract_information(soup, '勤務地'),
                '雇用形態': self.extract_information(soup, '雇用形態'),
                '勤務時間': self.extract_information(soup, '勤務時間'),
                '給与': self.extract_information(soup, '給与'),
                '待遇・福利厚生': self.extract_information(soup, '待遇・福利厚生'),
                '休日・休暇': self.extract_information(soup, '休日・休暇'),
                '会社概要': self.extract_information(soup, '会社概要'),
                '応募方法': self.extract_information(soup, '応募方法')
            }

            return details

        except Exception as e:
            logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
            raise
        finally:
            self.quit_driver()

    def extract_information(self, soup, section_title):
        section = soup.find('th', text=lambda text: section_title in text)
        if section:
            content = section.find_next_sibling('td')
            return content.get_text(strip=True) if content else 'Not Found'
        return 'Not Found'
