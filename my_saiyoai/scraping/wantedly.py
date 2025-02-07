from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

def scrape_wantedly(job_url):
    # クロームドライバーのパスを設定
    webdriver_path = os.getenv('PATH_TO_WEBDRIVER')
    s = Service(webdriver_path)

    # Chromeオプションを設定
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # ウェブドライバーのインスタンスを作成
    driver = webdriver.Chrome(service=s, options=options)
    try:
        driver.get(job_url)

        # ページのソースを取得
        page_source = driver.page_source

        # BeautifulSoupを使用してHTMLを解析
        soup = BeautifulSoup(page_source, 'html.parser')

        # ストーリーセクションの抽出
        story_section = soup.find('section', {'id': 'story'})
        if not story_section:
            story_text = "ストーリーセクションが見つかりませんでした。"
        else:
            story_text = story_section.find('p').get_text(strip=True)

        # 価値観セクションの抽出
        values_section = soup.find('section', {'id': 'values'})
        if not values_section:
            values_text = "価値観セクションが見つかりませんでした。"
        else:
            values_items = values_section.find_all('div', class_='CompanyValueGridItem__Wrapper-sc-17vy9ug-0')
            values_texts = []
            for item in values_items:
                title = item.find('div', class_='CompanyValueGridItem__Title-sc-17vy9ug-2').get_text(strip=True)
                description = item.find('div', class_='CompanyValueGridItem__Description-sc-17vy9ug-5').get_text(strip=True)
                values_texts.append(f"{title}: {description}")
            values_text = "\n".join(values_texts)

        return story_text, values_text

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error occurred while scraping Wantedly: {e}")
        return None, None
    finally:
        driver.quit()
