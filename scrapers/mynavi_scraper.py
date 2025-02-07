# mynavi_scraper.py
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class MynaviScraper(BaseScraper):
    def scrape(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
            soup = BeautifulSoup(outer_html, 'html.parser')

            details = {
                '求人サマリー': self.extract_information(soup, "body > div.wrapper > div.container.container-jobinfo > div:nth-child(4) > div.jobPointArea.js__followButtonRange--from > div > div"),
                '仕事内容': self.extract_information(soup, "#parts_job_description"),
                '対象となる方': self.extract_information(soup, "#parts_target_person"),
                '募集要項': self.extract_information(soup, "body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > table:nth-child(9)"),
                '企業の特徴': self.extract_information(soup, "body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div:nth-child(39)"),
                '会社概要': self.extract_information(soup, "body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > table.jobOfferTable.thL")
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
