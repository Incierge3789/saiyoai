from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import os

def scrape_mynavi(job_url):
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

        # 求人のポイントセクションの抽出
        job_point_section = soup.find('section', {'id': 'jobInfo1'})
        if not job_point_section:
            job_point_text = "この求人のポイントセクションが見つかりませんでした。"
        else:
            job_point_text = job_point_section.get_text(strip=True)

        # 仕事内容セクションの抽出
        job_description_section = soup.find('section', {'id': 'jobInfo2'})
        if not job_description_section:
            job_description_text = "仕事内容セクションが見つかりませんでした。"
        else:
            job_description_text = job_description_section.get_text(strip=True)

        # 対象となる方セクションの抽出
        target_person_section = soup.find('section', {'id': 'jobInfo3'})
        if not target_person_section:
            target_person_text = "対象となる方セクションが見つかりませんでした。"
        else:
            target_person_text = target_person_section.get_text(strip=True)

        # 募集要項セクションの抽出
        job_requirements_section = soup.find('section', {'id': 'jobInfo4'})
        if not job_requirements_section:
            job_requirements_text = "募集要項セクションが見つかりませんでした。"
        else:
            job_requirements_text = job_requirements_section.get_text(strip=True)

        # 会社情報セクションの抽出
        company_info_section = soup.find('section', {'id': 'jobInfo5'})
        if not company_info_section:
            company_info_text = "会社情報セクションが見つかりませんでした。"
        else:
            company_info_text = company_info_section.get_text(strip=True)

        return job_point_text, job_description_text, target_person_text, job_requirements_text, company_info_text

    except (TimeoutException, NoSuchElementException) as e:
        print(f"Error occurred while scraping MyNavi: {e}")
        return None, None, None, None, None
    finally:
        driver.quit()
