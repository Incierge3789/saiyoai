from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

def scrape_doda(job_url):
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

        # <h1> タグから会社名を含むテキストを抽出
        h1_tag = soup.find('h1')
        if h1_tag:
            company_name_text = h1_tag.get_text(strip=True)
        else:
            company_name_text = "会社名が見つかりませんでした。"

        # 各セクションの内容を抽出する関数
        def extract_section_by_title(section_title):
            section = soup.find(lambda tag: tag.name == "th" and section_title in tag.get_text())
            if section:
                next_td = section.find_next_sibling('td')
                if next_td:
                    return next_td.get_text().strip()
            return f"セクション '{section_title}' が見つかりませんでした。"

        # 抽出したいセクションタイトルをリストに入れる
        section_titles = ['仕事内容', '対象となる方', '勤務地', '勤務時間', '雇用形態', '給与', '待遇・福利厚生', '休日・休暇']

        # 各セクションの内容を抽出
        sections_text = [extract_section_by_title(section_title) for section_title in section_titles]

        return company_name_text, *sections_text

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error occurred while scraping doda: {e}")
        return None, None, None, None, None, None, None, None, None
    finally:
        driver.quit()
