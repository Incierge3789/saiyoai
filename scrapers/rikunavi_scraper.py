# rikunavi_scraper.py
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class RikunaviScraper(BaseScraper):
    def scrape(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
            soup = BeautifulSoup(outer_html, 'html.parser')

            details = {
                '求人オファーヘッダー': self.extract_information(soup, "div.rn3-companyOfferHeader__main > h1"),
                '求人オファータグ': self.extract_information(soup, "div.rn3-companyOfferHeader__main > ul"),
                '求人オファーテキスト': self.extract_information(soup, "div.rn3-companyOfferHeader__main > p"),
                '仕事の概要タイトル': self.extract_information(soup, "span.rn3-topSummaryTitle"),
                '仕事の概要サマリーテキスト': self.extract_information(soup, "div.rn3-companyOffer__mpSummary > div:nth-child(1) > p"),
                '勤務地タイトル': self.extract_information(soup, "span.rn3-topSummaryTitle"),
                '勤務地テキスト': self.extract_information(soup, "div.rn3-companyOffer__mpSummary > div:nth-child(2) > p"),
                '年収例タイトル': self.extract_information(soup, "span.rn3-topSummaryTitle"),
                '年収例サマリー': self.extract_information(soup, "div.rn3-companyOffer__mpSummary > div:nth-child(3) > p"),
                '休日・休暇タイトル': self.extract_information(soup, "span.rn3-topSummaryTitle"),
                '休日・休暇サマリー': self.extract_information(soup, "div.rn3-companyOffer__mpSummary > div:nth-child(4) > p"),
                '募集要項タイトル': self.extract_information(soup, "div.rn3-companyOfferContent__section > h2"),
                '募集要項テキスト': self.extract_information(soup, "div.rn3-companyOfferRecruitment__head > div"),
                '仕事内容タイトル': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(2) > h3"),
                '仕事内容テキスト': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(2) > div"),
                '求めている人材タイトル': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(3) > h3"),
                '求めている人材テキスト': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(3) > div"),
                '給与タイトル': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(5) > h3"),
                '給与テキスト': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(5) > div"),
                '勤務時間タイトル': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(6) > h3"),
                '勤務時間テキスト': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(6) > div"),
                '福利厚生タイトル': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(8) > h3"),
                '福利厚生テキスト': self.extract_information(soup, "div.rn3-companyOfferRecruitment > div:nth-child(8) > div")
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
