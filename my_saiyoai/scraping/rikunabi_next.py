from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

def scrape_rikunavi(job_url):
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

        # 特定のIDやクラスを持つ要素のテキストを抽出する関数
        def extract_text_by_id_or_class(id_or_class):
            elements = soup.find_all(lambda tag: (tag.get('id') == id_or_class or id_or_class in tag.get('class', [])))
            if elements:
                return "\n".join([element.get_text(strip=True) for element in elements])
            else:
                return f"IDまたはクラス '{id_or_class}' の要素が見つかりませんでした。"

        # 抽出したいIDまたはクラスをリストに入れる
        ids_or_classes = [
            'rn3-companyOfferBreadcrumbs__item',  # 求人情報のリスト項目
            'rn3-companyOfferInfo__message',      # 応募呼びかけのメッセージ
            'rn3-companyOfferHeader__main',       # 求人情報のヘッダー
            'rn3-topSummaryElement',              # 仕事内容の概要
            'rn3-companyOfferRecruitment__info',  # 仕事内容、求めている人材、勤務地、給与、勤務時間、休日・休暇、待遇・福利厚生
            'rn3-companyOfferInterview',          # 社員インタビュー
            'rn3-companyOfferAcquire',            # 職場環境・風土
            'rn3-companyOfferCompany',            # 企業概要
            'rn3-companyOfferEntry'               # 応募について
        ]

        # 各IDまたはクラスに対応する要素の内容を抽出
        extracted_texts = [extract_text_by_id_or_class(id_or_class) for id_or_class in ids_or_classes]

        return extracted_texts

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error occurred while scraping rikunavi: {e}")
        return None
    finally:
        driver.quit()
