from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

def scrape_entenshoku(job_url):
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
                return "\n".join([element.get_text(strip=True).replace('<br/>', '') for element in elements])
            else:
                return f"IDまたはクラス '{id_or_class}' の要素が見つかりませんでした。"

        # 抽出したいIDまたはクラスをリストに入れる
        ids_or_classes = [
            "seoPageTitle", "descFixedButtonArea", "job", "company", "descWriterSet descWriterSet--icon",
            "descTab", "tabList", "descCompanyName", "descJobName", "descCatchArea", "photoArea", "copyArea",
            "descArticleUnit dataWork", "item job", "item capacity", "item backbone", "item user", "item area",
            "item time", "item money", "item vacation", "item benefit", "item option",
            "descPhotoArea", "descStaffPointArea", "descArticleUnit dataCompanyInfoSummary"
        ]

        # 各IDまたはクラスに対応する要素の内容を抽出
        extracted_texts = [extract_text_by_id_or_class(id_or_class) for id_or_class in ids_or_classes]

        return extracted_texts

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error occurred while scraping entenshoku: {e}")
        return None
    finally:
        driver.quit()
