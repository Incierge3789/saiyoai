from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

def scrape_indeed(job_url):
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

        # 特定のクラスを持つ要素のテキストを抽出する関数
        def extract_text_until_br(class_name):
            element = soup.find(class_=class_name)
            if element:
                text = ''.join(str(child) for child in element.parent.contents)
                text_until_br = text.split("<br>", 1)[0]
                text_without_br = text_until_br.replace('<br/>', '')
                return text_without_br
            else:
                return f"クラス '{class_name}' の要素が見つかりませんでした。"

        # 抽出したいクラスをリストに入れる
        classes_to_extract = [
            "jobSectionHeader",  # 求人の見出し
            "jobsearch-jobDescriptionText"  # 求人の詳細
        ]

        # 各クラスに対応する要素の内容を抽出
        extracted_texts = [extract_text_until_br(class_name) for class_name in classes_to_extract]

        return extracted_texts

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error occurred while scraping indeed: {e}")
        return None
    finally:
        driver.quit()
