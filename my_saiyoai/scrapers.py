from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import os
import hashlib
import logging
from .utils import clean_text
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

logger = logging.getLogger(__name__)

def initialize_driver():
    options = webdriver.ChromeOptions()
    webdriver_path = os.getenv('PATH_TO_WEBDRIVER')
    chrome_binary_path = os.getenv('CHROME_BINARY_PATH')  # 環境変数からChromeのパスを取得
    service = Service(webdriver_path)
    
    if chrome_binary_path:
       options.binary_location = chrome_binary_path  # Chromeのバイナリパスを指定

    options.add_argument('--headless')
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")  # ウィンドウサイズを指定
    options.add_argument("--start-maximized")  # 最大化
    options.add_argument("--disable-extensions")  # 拡張機能を無効にする
     # ユーザーエージェントを変更
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36")


    return webdriver.Chrome(service=service, options=options)


def quit_driver(driver):
    driver.quit()


def get_content_from_url(url, driver):
    try:
        logger.debug(f"Attempting to scrape URL: {url}")
        driver.get(url)
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        cleaned_text = clean_text(text)
        logger.debug(f"Scraped and cleaned text: {cleaned_text[:100]}...")
        return cleaned_text
    except (WebDriverException, NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
        raise

def retryable_operation(function, max_attempts=5, initial_wait=1.0, backoff_factor=2):
    attempts = 0
    wait_time = initial_wait
    while attempts < max_attempts:
        try:
            return function()
        except (WebDriverException, Exception) as e:
            logger.warning(f"Operation failed with error '{e}', attempt {attempts + 1} of {max_attempts}")
            time.sleep(wait_time)
            attempts += 1
            wait_time *= backoff_factor
    raise Exception(f"All {max_attempts} attempts failed")


def scrape_default(url):
    driver = initialize_driver()
    try:
        driver.get(url)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        text = soup.get_text()
        cleaned_text = clean_text(text)
        return cleaned_text
    except Exception as e:
        logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
        return f"Error during scraping: {str(e)}"
    finally:
        driver.quit()


def extract_information(soup, section_title):
    section = soup.find('th', text=lambda text: section_title in text)
    if section:
        content = section.find_next_sibling('td')
        return content.get_text(strip=True) if content else 'Not Found'
    return 'Not Found'

# HTMLソースを保存する関数の定義
def save_html_source(html_source, file_name, site_name):
    base_directory = '/home/silver.and.gold13579/saiyoai1/saiyoai/scraping_results'
    save_directory = os.path.join(base_directory, site_name)  # サイト名を含むディレクトリパス

    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    file_path = os.path.join(save_directory, file_name)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html_source)
    logger.info(f"HTML source saved to {file_path}")

def generate_file_name_from_url(url):
    # URLからハッシュ値を生成し、ファイル名として使用
    hash_object = hashlib.md5(url.encode())
    file_name = hash_object.hexdigest() + '.html'
    return file_name

def remove_unnecessary_characters(text):
    # 不要なスペース、改行、特殊文字を削除
    #cleaned_text = re.sub(r'\s+', ' ', text)  # すべての空白文字を単一スペースに置換
    cleaned_text = re.sub(r'[ \t]+', ' ', text)
    return cleaned_text

def remove_duplicates(sections):
    seen_hashes = set()
    seen_start_words = {}
    unique_sections = []

    # まずハッシュに基づいて重複をチェック
    for section in sections:
        section_hash = hash(section)
        if section_hash not in seen_hashes:
            seen_hashes.add(section_hash)
            unique_sections.append(section)

    # ハッシュに基づくチェック後のセクションで、文頭に基づいて重複をチェック
    # この段階では、より長いセクションを保持
    for section in unique_sections:
        start_words = ' '.join(section.split()[:10])
        if start_words in seen_start_words:
            # 既存のセクションと長さを比較
            if len(section) > len(seen_start_words[start_words]):
                seen_start_words[start_words] = section
        else:
            seen_start_words[start_words] = section

    # 最長のセクションのみを保持
    final_sections = list(seen_start_words.values())
    return final_sections


def scrape_doda(job_url):
    driver = initialize_driver()
    
    try:

        # 求人ページへアクセス
        logger.info(f"Scraping Doda job posting at {job_url}")
        driver.get(job_url)

        # ページ読み込みの完了を待機
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        logger.info("Page load complete")

       # HTMLソースを保存
        outer_html = driver.execute_script("return document.documentElement.outerHTML")
        file_name = generate_file_name_from_url(job_url)  # URLに基づいてファイル名を生成
        site_name = "doda"  # サイト名
        save_html_source(outer_html, file_name, site_name)  # サイト名を引数として渡す


        # HTMLを取得し、解析
        outer_html = driver.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(outer_html, 'html.parser')

        # CSSセレクターを使用して「関連情報」セクション以降を削除
        related_info_css = soup.select_one("#shStart > article > div.related_information.shtRelLink > h2")
        if related_info_css:
            related_info_css.extract()

        # 「関連情報」セクションの特定
        related_info_section = soup.find('h2', text='関連情報')
        if related_info_section:
            # 「関連情報」セクション以降を削除
            index = str(soup).find(str(related_info_section))
            if index != -1:
                modified_html = str(soup)[:index]
                soup = BeautifulSoup(modified_html, 'html.parser')
        
        # 情報抽出のための項目リストを更新
        contents_list = [
            '企業情報',
            '仕事内容',
            '対象となる方',
            '勤務地',
            '雇用形態',
            '勤務時間',
            '給与',
            '待遇・福利厚生',
            '休日・休暇',
            '会社概要',
            '応募方法',
            # 追加したい他の項目
        ]

        detail_dict = {}

        for content in contents_list:
            try:
                if content == "企業情報":
                    # 企業名とその説明文を抽出
                    company_info_selector = "#wrapper > div.head_detail > div > div > h1"
                    company_info_element = soup.select_one(company_info_selector)
                    if company_info_element:
                        company_name = company_info_element.text.strip()
                        company_description = company_info_element.find("span", class_="explain").text.strip() if company_info_element.find("span", class_="explain") else ""
                        detail_dict['企業情報'] = f"{company_name}\n{company_description}"
                    else:
                        detail_dict['企業情報'] = 'Not Found'
                # CSSセレクターで情報を取得
                css_selector = f"div#shtTabContent1 div#shtTabInner2 div.layout table.tblDetail01 tbody tr th:contains('{content}') + td"
                content_element = soup.select_one(css_selector)
                if content_element:
                    detail_dict[content] = content_element.get_text(strip=True)
                elif content == "会社概要":
                    # 「会社概要」の情報を特別なセレクターで取得
                    company_details_selector = "#shtTabInner3 > div.layout > div.modDetail04"
                    company_details_element = soup.select_one(company_details_selector)
                    detail_dict[content] = company_details_element.get_text(separator="\n", strip=True) if company_details_element else 'Not Found'
                else:
                    # CSSセレクターで見つからない場合、XPathを使用
                    xpath = f"//div[@id='shtTabContent1']/div[@id='shtTabInner2']/div[@class='layout']/table[@class='tblDetail01']/tbody/tr/th[contains(text(), '{content}')]/following-sibling::td"
                    content_element = driver.find_element(By.XPATH, xpath)
                    detail_dict[content] = content_element.text.replace("\n", "")
            except (NoSuchElementException, Exception) as e:
                detail_dict[content] = 'Not Found'

            # 「応募方法」セクションが見つかったらループを終了
            if content == '応募方法':
                break


        # 抽出された情報を文字列として結合
        scraped_text = '\n'.join([f"{key}: {value}" for key, value in detail_dict.items()])

        # ここにクリーニング処理を挿入
        cleaned_text = remove_unnecessary_characters(scraped_text)

        # クリーニングされたテキストを返す
        return cleaned_text

        # 抽出された情報が不足している場合、フォールバック処理を実行
        if 'Not Found' in scraped_text:
            return scrape_default(job_url)

        return scraped_text

    except TimeoutException:
        logger.error("Page load timed out")
        return "Error: Page load timed out"
    except NoSuchElementException:
        logger.error("Element not found")
        return "Error: Element not found"
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return f"Error: {e}"
    finally:
        quit_driver(driver)

    return "Error: Unable to scrape the job posting"

def scrape_entenshoku(job_url):
    driver = initialize_driver()

    try:
        logger.info(f"Starting scraping En-Tenshoku job posting at {job_url}")
        
        # ページへアクセス
        driver.get(job_url)

        # ページ読み込み完了を待機
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # HTMLを取得し、解析
        outer_html = driver.execute_script("return document.documentElement.outerHTML")

        # HTMLソースを保存
        file_name = generate_file_name_from_url(job_url)  # URLに基づいてファイル名を生成
        site_name = "entenshoku"  # サイト名
        save_html_source(outer_html, file_name, site_name)  # サイト名を引数として渡す

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(outer_html, 'html.parser')

        #ids_or_classes = {
            #"seoPageTitle": "#seoPageTitle",
            #"descJobName": "#descJobName",
            #"descCatchArea": "#descCatchArea",
            #"recruitment_details": "body > div.pageSet > div:nth-child(3) > div.descArticleUnit.dataWork",
            #"company_overview": "body > div.pageSet > div:nth-child(5) > div"
        #}

        # 募集情報の抽出
        catch = soup.select_one("#descCatchArea > div > div.catch").get_text(strip=True)
        copy = soup.select_one("#descCatchArea > div > div.copy").get_text(strip=True)

        # 募集要項の抽出
        recruitment_titles = soup.select("body > div.pageSet > div:nth-child(3) > div.descArticleUnit.dataWork > div.contents > table > tbody > tr > th")
        recruitment_contents = soup.select("body > div.pageSet > div:nth-child(3) > div.descArticleUnit.dataWork > div.contents > table > tbody > tr > td")
        recruitment_details = {title.get_text(strip=True): content.get_text(strip=True) for title, content in zip(recruitment_titles, recruitment_contents)}

        # 会社概要の抽出
        company_titles = soup.select("body > div.pageSet > div:nth-child(5) > div > div.contents > table > tbody > tr > th")
        company_contents = soup.select("body > div.pageSet > div:nth-child(5) > div > div.contents > table > tbody > tr > td")
        company_overview = {title.get_text(strip=True): content.get_text(strip=True) for title, content in zip(company_titles, company_contents)}

        # 結果の結合
        scraped_text = f"募集情報:\nCatch: {catch}\nCopy: {copy}\n\n募集要項:\n" + "\n".join([f"{key}: {value}" for key, value in recruitment_details.items()])
        scraped_text += "\n\n会社概要:\n" + "\n".join([f"{key}: {value}" for key, value in company_overview.items()])

        # ここにクリーニング処理を挿入（例：HTMLタグの除去など）
        cleaned_text = remove_unnecessary_characters(scraped_text)

        # 抽出された情報が不足している場合、フォールバック処理を実行
        if 'Not Found' in cleaned_text:
            return scrape_default(job_url)  # フォールバック関数は別途定義が必要

        return cleaned_text

    except (WebDriverException, NoSuchElementException) as e:
        logger.error(f"Error occurred while scraping En-Tenshoku job posting: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error occurred while scraping: {e}")
        return {"error": "Unexpected error"}
    finally:
        quit_driver(driver)

def scrape_indeed(job_url):
    driver = initialize_driver()

    try:
        logger.info(f"Indeedの求人情報をスクレイピング開始: {job_url}")

        # ページへのアクセス
        driver.get(job_url)

        # ページ読み込みの完了を待機
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # HTMLソースの取得
        outer_html = driver.execute_script("return document.documentElement.outerHTML")

        # HTMLソースの保存
        file_name = generate_file_name_from_url(job_url)
        site_name = "indeed"
        save_html_source(outer_html, file_name, site_name)

        # HTMLの解析
        soup = BeautifulSoup(outer_html, 'html.parser')

        # 情報の抽出
        job_title = soup.select_one(".jobsearch-JobInfoHeader-title").get_text(strip=True) if soup.select_one(".jobsearch-JobInfoHeader-title") else "求人タイトルが見つかりません"
        company_name = soup.select_one(".jobsearch-InlineCompanyRating > div:first-child").get_text(strip=True) if soup.select_one(".jobsearch-InlineCompanyRating > div:first-child") else "企業名が見つかりません"
        location = soup.select_one(".jobsearch-InlineCompanyRating > div:last-child").get_text(strip=True) if soup.select_one(".jobsearch-InlineCompanyRating > div:last-child") else "勤務地が見つかりません"
        job_description = soup.select_one(".jobsearch-jobDescriptionText").get_text(strip=True) if soup.select_one(".jobsearch-jobDescriptionText") else "仕事内容が見つかりません"

        # 情報の結合
        scraped_text = f"求人タイトル: {job_title}\n企業名: {company_name}\n勤務地: {location}\n仕事内容: {job_description}"

        # テキストのクリーニング
        cleaned_text = remove_unnecessary_characters(scraped_text)

        logger.info("Indeedの求人情報を正常にスクレイピングしました")
        return cleaned_text

    except (WebDriverException, NoSuchElementException) as e:
        logger.error(f"Indeedの求人情報のスクレイピング中にエラー発生: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        return {"error": "予期せぬエラー"}
    finally:
        quit_driver(driver)


def scrape_mynavi(job_url):
    driver = initialize_driver()

    try:
        logger.info(f"Starting scraping MyNavi job posting at {job_url}")

        # ページへアクセス
        driver.get(job_url)

        # ページ読み込み完了を待機
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # HTMLを取得し、解析
        outer_html = driver.execute_script("return document.documentElement.outerHTML")

        # HTMLソースを保存
        file_name = generate_file_name_from_url(job_url)  # URLに基づいてファイル名を生成
        site_name = "mynavi"  # サイト名
        save_html_source(outer_html, file_name, site_name)  # サイト名を引数として渡す

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(outer_html, 'html.parser')
        
        # セクションの抽出とエラーハンドリング
        def get_section_text(selector, error_message):
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else error_message

        job_summary_section = get_section_text("body > div.wrapper > div.container.container-jobinfo > div:nth-child(4) > div.jobPointArea.js__followButtonRange--from > div > div", "求人サマリーセクションが見つかりませんでした。")
        job_description = get_section_text("#parts_job_description", "仕事内容セクションが見つかりませんでした。")
        target_person = get_section_text("#parts_target_person", "対象となる方セクションが見つかりませんでした。")
        job_requirements = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > table:nth-child(9)", "募集要項セクションが見つかりませんでした。")
        company_features = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div:nth-child(39)", "企業の特徴セクションが見つかりませんでした。")
        company_overview = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > table.jobOfferTable.thL", "会社概要セクションが見つかりませんでした。")
        
        recruitment_background = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div.jobPointArea__body.jobPointArea__body-prArea > div > h4", "募集背景セクションが見つかりませんでした。")
        job_summary_description = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div.jobPointArea__wrap-jobDescription > div.jobPointArea__head", "仕事内容の要約セクションが見つかりませんでした。")
        specific_job_details = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div.jobPointArea__wrap-jobDescription > h3", "具体的な仕事内容セクションが見つかりませんでした。")
        main_job_description = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div.jobPointArea__wrap-jobDescription > div.jobPointArea__body", "仕事内容の本文セクションが見つかりませんでした。")
        target_person_summary = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div.jobPointArea__head", "対象となる方の要約セクションが見つかりませんでした。")
        target_person_details = get_section_text("body > div.wrapper > div.container.container-jobinfo > div.container__inner.lightBlue > div > div.jobPointArea__mainWrap > div.leftBlock.clearfix > div.jobPointArea__body--large", "対象となる方の詳細セクションが見つかりませんでした。")

        # 追加セクションの抽出
        job_info = get_section_text("body > div.wrapper > div.container.container-jobinfo > div:nth-child(2) > div > div.cassetteOfferRecapitulate__content.cassetteOfferRecapitulate__content-jobinfo > div.blockWrapper > div.rightBlock", "求人情報が見つかりませんでした。")
        occ_name = get_section_text("body > div.wrapper > div.container.container-jobinfo > div:nth-child(2) > div > div.cassetteOfferRecapitulate__content.cassetteOfferRecapitulate__content-jobinfo > div.blockWrapper > div.rightBlock > h1 > span.occName", "職種名が見つかりませんでした。")
        company_name = get_section_text("body > div.wrapper > div.container.container-jobinfo > div:nth-child(2) > div > div.cassetteOfferRecapitulate__content.cassetteOfferRecapitulate__content-jobinfo > div.blockWrapper > div.rightBlock > h1 > span.companyName", "企業名が見つかりませんでした。")
        company_name_add = get_section_text("body > div.wrapper > div.container.container-jobinfo > div:nth-child(2) > div > div.cassetteOfferRecapitulate__content.cassetteOfferRecapitulate__content-jobinfo > div.blockWrapper > div.rightBlock > h1 > span.companyNameAdd", "企業名の追加情報が見つかりませんでした。")


        # 情報の結合
        scraped_text = (
            f"求人情報: {job_info}\n"
            f"職種名: {occ_name}\n"
            f"企業名: {company_name}\n"
            f"企業名追加情報: {company_name_add}\n"
            f"求人サマリー: {job_summary_section}\n"
            f"募集背景: {recruitment_background}\n"
            f"仕事内容の要約: {job_summary_description}\n"
            f"具体的な仕事内容: {specific_job_details}\n"
            f"仕事内容の本文: {main_job_description}\n"
            f"対象となる方: {target_person}\n"
            f"対象となる方の要約: {target_person_summary}\n"
            f"対象となる方の詳細: {target_person_details}\n"
            f"募集要項: {job_requirements}\n"
            f"企業の特徴: {company_features}\n"
            f"会社概要: {company_overview}"
        )



        # テキストのクリーニング
        cleaned_text = remove_unnecessary_characters(scraped_text)
        
        # 抽出された情報が不足している場合、フォールバック処理を実行
        if 'Not Found' in cleaned_text:
            return scrape_default(job_url)  # フォールバック関数は別途定義が必要

        logger.info("MyNaviの求人情報を正常にスクレイピングしました")
        return cleaned_text

    except WebDriverException as e:
        logger.error(f"Error occurred while scraping MyNavi job posting: {e}")
        return {"error": str(e)}
    finally:
        quit_driver(driver)

def scrape_rikunavi(job_url):
    driver = initialize_driver()

    try:
        logger.info(f"Starting scraping Rikunavi job posting at {job_url}")
        driver.get(job_url)
        WebDriverWait(driver, 60).until(lambda d: d.execute_script("return document.readyState") == "complete")
        outer_html = driver.execute_script("return document.documentElement.outerHTML")
        file_name = generate_file_name_from_url(job_url)
        save_html_source(outer_html, file_name, "rikunavi")
        soup = BeautifulSoup(outer_html, 'html.parser')

        def get_section_text(selector, error_message):
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else error_message

        # Extracting new elements
        job_offer_header = get_section_text("div.rn3-companyOfferHeader__main > h1", "求人オファーヘッダーが見つかりませんでした。")
        job_offer_tags = get_section_text("div.rn3-companyOfferHeader__main > ul", "求人オファータグが見つかりませんでした。")
        job_offer_text = get_section_text("div.rn3-companyOfferHeader__main > p", "求人オファーテキストが見つかりませんでした。")
        # [Add additional selectors here]
        job_summary_title = get_section_text("span.rn3-topSummaryTitle", "仕事の概要タイトルが見つかりませんでした。")
        job_summary_text = get_section_text("div.rn3-companyOffer__mpSummary > div:nth-child(1) > p", "仕事の概要サマリーテキストが見つかりませんでした。")

        # 続きのセレクター抽出
        work_location_title = get_section_text("span.rn3-topSummaryTitle", "勤務地タイトルが見つかりませんでした。")
        work_location_text = get_section_text("div.rn3-companyOffer__mpSummary > div:nth-child(2) > p", "勤務地テキストが見つかりませんでした。")
        salary_example_title = get_section_text("span.rn3-topSummaryTitle", "年収例タイトルが見つかりませんでした。")
        salary_example_text = get_section_text("div.rn3-companyOffer__mpSummary > div:nth-child(3) > p", "年収例サマリーが見つかりませんでした。")
        # その他のセレクター抽出
        holiday_vacation_title = get_section_text("span.rn3-topSummaryTitle", "休日・休暇タイトルが見つかりませんでした。")
        holiday_vacation_text = get_section_text("div.rn3-companyOffer__mpSummary > div:nth-child(4) > p", "休日・休暇サマリーが見つかりませんでした。")
        recruitment_section_title = get_section_text("div.rn3-companyOfferContent__section > h2", "募集要項タイトルが見つかりませんでした。")
        recruitment_section_text = get_section_text("div.rn3-companyOfferRecruitment__head > div", "募集要項テキストが見つかりませんでした。")
        # その他のセレクター抽出
        job_content_title = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(2) > h3", "仕事内容のタイトルが見つかりませんでした。")
        job_content_text = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(2) > div", "仕事内容のテキストが見つかりませんでした。")
        desired_person_title = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(3) > h3", "求めている人材のタイトルが見つかりませんでした。")
        desired_person_text = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(3) > div", "求めている人材のテキストが見つかりませんでした。")
        salary_title = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(5) > h3", "給与のタイトルが見つかりませんでした。")
        salary_text = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(5) > div", "給与のテキストが見つかりませんでした。")
        working_hours_title = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(6) > h3", "勤務時間のタイトルが見つかりませんでした。")
        working_hours_text = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(6) > div", "勤務時間のテキストが見つかりませんでした。")
        welfare_title = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(8) > h3", "福利厚生のタイトルが見つかりませんでした。")
        welfare_text = get_section_text("div.rn3-companyOfferRecruitment > div:nth-child(8) > div", "福利厚生のテキストが見つかりませんでした。")

        # 職場環境・風土に関するセクションの抽出
        workplace_environment_title = get_section_text("div.rn3-companyOfferAcquire.js-acquire.is-moreTopClose > h3", "職場環境・風土についてのタイトルが見つかりませんでした。")
        workplace_environment_text = get_section_text("div.rn3-companyOfferAcquire.js-acquire.is-moreTopClose > div > div", "職場環境・風土についてのテキストが見つかりませんでした。")

        # 企業概要に関するセクションの抽出
        company_overview_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > h2", "企業概要のタイトルが見つかりませんでした。")
        company_name_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(1) > h3", "社名のタイトルが見つかりませんでした。")
        company_name_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(1) > p", "社名のテキストが見つかりませんでした。")
        establishment_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(2) > h3", "設立のタイトルが見つかりませんでした。")
        establishment_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(2) > p", "設立のテキストが見つかりませんでした。")

        # 追加のセクション抽出
        representative_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(3) > h3", "代表者のタイトルが見つかりませんでした。") 
        representative_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(3) > p", "代表者のテキストが見つかりませんでした。")
        sales_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(4) > h3", "売上高のタイトルが見つかりませんでした。")
        sales_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(4) > p", "売上高のテキストが見つかりませんでした。")
        employee_count_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(5) > h3", "従業員数のタイトルが見つかりませんでした。")
        employee_count_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(5) > p", "従業員数のテキストが見つかりませんでした。")

        # 追加のセクション抽出
        office_location_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(6) > h3", "事業所のタイトルが見つかりませんでした。")
        office_location_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(6) > p", "事業所のテキストが見つかりませんでした。")
        industry_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(7) > h3", "業種のタイトルが見つかりませんでした。")
        industry_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(7) > p", "業種のテキストが見つかりませんでした。")
        business_content_title = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(8) > h3", "事業内容のタイトルが見つかりませんでした。")
        business_content_text = get_section_text("div.rn3-companyOfferContent__section.js-cmpnyInfo > div > div:nth-child(8) > p", "事業内容のテキストが見つかりませんでした。")

        # Combining extracted texts
        scraped_text = (
            f"求人オファーヘッダー: {job_offer_header}\n"
            f"求人オファータグ: {job_offer_tags}\n"
            f"求人オファーテキスト: {job_offer_text}\n" 
            f"仕事の概要タイトル: {job_summary_title}\n"
            f"仕事の概要サマリーテキスト: {job_summary_text}\n"
            f"勤務地タイトル: {work_location_title}\n"
            f"勤務地テキスト: {work_location_text}\n"
            f"年収例タイトル: {salary_example_title}\n"
            f"年収例サマリー: {salary_example_text}\n"
            f"休日・休暇タイトル: {holiday_vacation_title}\n"
            f"休日・休暇サマリー: {holiday_vacation_text}\n"
            f"募集要項タイトル: {recruitment_section_title}\n"
            f"募集要項テキスト: {recruitment_section_text}\n"
            f"仕事内容: {job_content_title}\n"
            f"仕事内容テキスト: {job_content_text}\n"
            f"求めている人材: {desired_person_title}\n"
            f"求めている人材テキスト: {desired_person_text}\n"
            f"勤務地: {work_location_title}\n"
            f"勤務地テキスト: {work_location_text}\n"
            f"給与: {salary_title}\n"
            f"給与テキスト: {salary_text}\n"
            f"勤務時間: {working_hours_title}\n"
            f"勤務時間テキスト: {working_hours_text}\n"
            f"休日休暇: {holiday_vacation_title}\n"
            f"休日休暇テキスト: {holiday_vacation_text}\n"
            f"福利厚生: {welfare_title}\n"
            f"福利厚生テキスト: {welfare_text}\n"
            f"職場環境・風土についてのタイトル: {workplace_environment_title}\n"
            f"職場環境・風土についてのテキスト: {workplace_environment_text}\n"
            f"企業概要のタイトル: {company_overview_title}\n"
            f"社名のタイトル: {company_name_title}\n"
            f"社名のテキスト: {company_name_text}\n"
            f"設立のタイトル: {establishment_title}\n"
            f"設立のテキスト: {establishment_text}\n"
            f"代表者のタイトル: {representative_title}\n"
            f"代表者のテキスト: {representative_text}\n"
            f"売上高のタイトル: {sales_title}\n"
            f"売上高のテキスト: {sales_text}\n"
            f"従業員数のタイトル: {employee_count_title}\n"
            f"従業員数のテキスト: {employee_count_text}\n"
            f"事業所のタイトル: {office_location_title}\n"
            f"事業所のテキスト: {office_location_text}\n"
            f"業種のタイトル: {industry_title}\n"
            f"業種のテキスト: {industry_text}\n"
            f"事業内容のタイトル: {business_content_title}\n"
            f"事業内容のテキスト: {business_content_text}\n"
        # [Concatenate other extracted texts here]
        )
        cleaned_text = remove_unnecessary_characters(scraped_text)
        
        # 抽出された情報が不足している場合、フォールバック処理を実行
        if 'Not Found' in cleaned_text:
            return scrape_default(job_url)  # フォールバック関数は別途定義が必要
        logger.info("Successfully scraped Rikunavi job posting")
        return cleaned_text


    except WebDriverException as e:
        logger.error(f"Error occurred while scraping Rikunavi job posting: {e}")
        return {"error": str(e)}
    finally:
        quit_driver(driver)


def scrape_wantedly(job_url):
    driver = initialize_driver()  # Assuming initialize_driver() sets up the Selenium WebDriver

    try:
        logging.info(f"Starting scraping Wantedly job posting at {job_url}")
        driver.get(job_url)
        WebDriverWait(driver, 60).until(lambda d: d.execute_script("return document.readyState") == "complete")
        # Wait for page to load...
        outer_html = driver.execute_script("return document.documentElement.outerHTML")
        file_name = generate_file_name_from_url(job_url)
        save_html_source(outer_html, file_name, "wantedly")
        soup = BeautifulSoup(outer_html, 'html.parser')
        
        wait = WebDriverWait(driver, 60)
        element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".ProjectPlainDescription__PlainDescription-sc-ay222f-0")))

        def get_section_text(soup, tag, class_name=None):
            if class_name:
                section = soup.find(tag, class_=class_name)
            else:
                section = soup.find(tag)
            if section:
                return section.get_text(strip=True)
            return "Section text not found."


        # Wantedly情報の抽出
        #wantedly_title = get_section_text("head > title", "タイトルが見つかりませんでした。")
        title_element = soup.find('title')
        wantedly_title = title_element.get_text(strip=True) if title_element else "タイトルが見つかりませんでした。"

        company_name_element = soup.find('div', class_='ProjectHeaderTitle__Base-sc-hxz754-0 gPbWSI')
        company_name = company_name_element.get_text(strip=True) if company_name_element else "会社名が見つかりませんでした。"

        # "何をやっているのか" というテキストを含むヘッダーを探す
        what_doing_header = soup.find('h3', string="なにをやっているのか")
        # 対応する説明部分を探す
        what_doing_description = what_doing_header.find_next('div', class_='ProjectPlainDescription__PlainDescription-sc-ay222f-0 kGSTXn')
        # テキストを取得する
        what_doing_text = what_doing_description.get_text(strip=True) if what_doing_description else "なにをやっているのかのテキストが見つかりませんでした。"

        # "なぜやるのか" というテキストを含むヘッダーを探す
        why_doing_header = soup.find('h3', string="なぜやるのか")
        # 対応する説明部分を探す
        why_doing_description = why_doing_header.find_next('div', class_='ProjectPlainDescription__PlainDescription-sc-ay222f-0 kGSTXn')
        # テキストを取得する
        why_doing_text = why_doing_description.get_text(strip=True) if why_doing_description else "なぜやるのかのテキストが見つかりませんでした。"

        # "どうやっているのか" というテキストを含むヘッダーを探す
        how_doing_header = soup.find('h3', string="どうやっているのか")
        # 対応する説明部分を探す
        how_doing_description = how_doing_header.find_next('div', class_='ProjectPlainDescription__PlainDescription-sc-ay222f-0 kGSTXn')
        # テキストを取得する
        how_doing_text = how_doing_description.get_text(strip=True) if how_doing_description else "どうやっているのかのテキストが見つかりませんでした。"

        # "こんなことやります" というテキストを含むヘッダーを探す
        what_we_do_header = soup.find('h3', string="こんなことやります")
        # 対応する説明部分を探す
        what_we_do_description = what_we_do_header.find_next('div', class_='ProjectPlainDescription__PlainDescription-sc-ay222f-0 kGSTXn')
        # テキストを取得する
        what_we_do_text = what_we_do_description.get_text(strip=True) if what_we_do_description else "こんなことやりますのテキストが見つかりませんでした。"


        company_names_element = soup.select_one("div.ProjectPageContainer__Page-sc-b79fe5-0.lgnPUE div.JobPostPage__Body-sc-114e25-2.khOxRO div.layouts__Sub-sc-33iw66-5.JobPostBody__LayoutSub-sc-114qu6a-0.kpPJMb.fKPcZX div.layouts__CompanySection-sc-33iw66-8.ixIzWD section div:nth-child(2) div")
        company_names = company_name_element.get_text(strip=True) if company_name_element else "企業名が見つかりませんでした。"

        company_website_element = soup.select_one("div.ProjectPageContainer__Page-sc-b79fe5-0.lgnPUE div.JobPostPage__Body-sc-114e25-2.khOxRO div.layouts__Sub-sc-33iw66-5.JobPostBody__LayoutSub-sc-114qu6a-0.kpPJMb.fKPcZX div.layouts__CompanySection-sc-33iw66-8.ixIzWD section div.CompanySection__LabelList-sc-tscb6r-7.jWwgGO div.CompanySection__LabelItem-sc-tscb6r-6.hDMWag a")
        company_website = company_website_element.get_text(strip=True) if company_website_element else "企業HPが見つかりませんでした。"

        establishment_date_element = soup.select_one("div.ProjectPageContainer__Page-sc-b79fe5-0.lgnPUE div.JobPostPage__Body-sc-114e25-2.khOxRO div.layouts__Sub-sc-33iw66-5.JobPostBody__LayoutSub-sc-114qu6a-0.kpPJMb.fKPcZX div.layouts__CompanySection-sc-33iw66-8.ixIzWD section div.CompanySection__LabelList-sc-tscb6r-7.jWwgGO div.CompanySection__LabelItem-sc-tscb6r-6.dmgGzP p")
        establishment_date = establishment_date_element.get_text(strip=True) if establishment_date_element else "設立日が見つかりませんでした。"

        staff_count_element = soup.select_one("div.ProjectPageContainer__Page-sc-b79fe5-0.lgnPUE div.JobPostPage__Body-sc-114e25-2.khOxRO div.layouts__Sub-sc-33iw66-5.JobPostBody__LayoutSub-sc-114qu6a-0.kpPJMb.fKPcZX div.layouts__CompanySection-sc-33iw66-8.ixIzWD section div.CompanySection__LabelList-sc-tscb6r-7.jWwgGO div.CompanySection__LabelItem-sc-tscb6r-6.laXdCw p")
        staff_count = staff_count_element.get_text(strip=True) if staff_count_element else "在籍人数が見つかりませんでした。"

        company_address_element = soup.select_one("div.ProjectPageContainer__Page-sc-b79fe5-0.lgnPUE div.JobPostPage__Body-sc-114e25-2.khOxRO div.layouts__Sub-sc-33iw66-5.JobPostBody__LayoutSub-sc-114qu6a-0.kpPJMb.fKPcZX div.layouts__CompanySection-sc-33iw66-8.ixIzWD section div.CompanySection__LabelList-sc-tscb6r-7.jWwgGO div.CompanySection__LabelItem-sc-tscb6r-6.goiutF p")
        company_address = company_address_element.get_text(strip=True) if company_address_element else "住所が見つかりませんでした。"


        # 結合されたテキスト
        scraped_text = (
            f"タイトル: {wantedly_title}\n"
            f"会社名: {company_name}\n"
            f"何をやっているのかテキスト: {what_doing_text}\n"
            f"なぜやるのかテキスト: {why_doing_text}\n"
            f"どうやっているのかテキスト: {how_doing_text}\n"
            f"こんなことやりますテキスト: {what_we_do_text}\n"
            f"企業名: {company_names}\n"
            f"企業HP: {company_website}\n"
            f"設立日: {establishment_date}\n"
            f"在籍人数: {staff_count}\n"
            f"住所: {company_address}\n"
        )

         # テキストのクリーニング
        cleaned_text = remove_unnecessary_characters(scraped_text)
        
        # 抽出された情報が不足している場合、フォールバック処理を実行
        if 'Not Found' in cleaned_text:
            return scrape_default(job_url)  # フォールバック関数は別途定義が必要


        logging.info("Successfully scraped Wantedly job posting")
        return cleaned_text
    
    except Exception as e:
        logging.error(f"Error occurred while scraping: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()


def scrape_wantedly_company(job_url):
    driver = initialize_driver()  # Assuming initialize_driver() sets up the Selenium WebDriver

    try:
        logging.info(f"Starting scraping Wantedly job posting at {job_url}")
        driver.get(job_url)
        WebDriverWait(driver, 60).until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        wait = WebDriverWait(driver, 60)
        element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#mission")))

        outer_html = driver.execute_script("return document.documentElement.outerHTML")
        file_name = generate_file_name_from_url(job_url)
        save_html_source(outer_html, file_name, "wantedly_company")
        soup = BeautifulSoup(outer_html, 'html.parser')

        def get_section_text(soup, tag, class_name=None):
            if class_name:
                section = soup.find(tag, class_=class_name)
            else:
                section = soup.find(tag)
            if section:
                return section.get_text(strip=True)
            return "Section text not found."

        # "ミッション" セクションのテキストを取得し、整理する
        mission_section = soup.find('section', id='mission')
        mission_text = "ミッション: " + (mission_section.get_text(strip=True) if mission_section else "情報なし")

        # "価値観" セクションのテキストを取得し、整理する
        values_section = soup.find('section', id='values')
        values_text = "価値観: " + (values_section.get_text(strip=True) if values_section else "情報なし")

        # 会社情報のセクションを取得
        basic_info_section = soup.find('section', id='basic_info')
        if basic_info_section:
            company_name = basic_info_section.find('div', class_='BasicInfoSection__CompanyName-sc-kk2ai9-5').get_text(strip=True)
            
            # SNSリンクを含まない詳細情報のリスト化
            info_items = basic_info_section.find_all('li', class_='BasicInfoSection__ListItem-sc-kk2ai9-9')
            info_items = [item for item in info_items if not item.find('div', class_='BasicInfoSection__SNSLinks-sc-kk2ai9-6')]

            # 詳細情報のリスト化
            info_items = basic_info_section.find_all('li', class_='BasicInfoSection__ListItem-sc-kk2ai9-9')

            # 各項目の取得
            address = info_items[0].div.get_text(strip=True) if len(info_items) > 0 else '情報なし'
            website = info_items[1].div.a['href'] if len(info_items) > 1 else '情報なし'
            establishment = info_items[2].div.get_text(strip=True) if len(info_items) > 2 else '情報なし'
            founder = info_items[3].div.get_text(strip=True) if len(info_items) > 3 else '情報なし'
            members = info_items[4].div.get_text(strip=True) if len(info_items) > 4 else '情報なし'
            funding_status = info_items[5].div.get_text(strip=True) if len(info_items) > 5 else '情報なし'

            # 会社情報の整理
            # 会社情報の辞書としての定義
            company_info = {
                "会社名": company_name,
                "住所": address,
                "ウェブサイト": website,
                "設立日": establishment,
                "創業者": founder,
                "メンバー数": members,
                "資金調達状況": funding_status
            }
        else:
            company_info = "会社情報セクションが見つかりませんでした。"
        
        # 辞書内の各要素に関数を適用
        cleaned_company_info = {key: remove_unnecessary_characters(value) for key, value in company_info.items()}

        # 辞書の内容を文字列として整形
        formatted_company_info = "\n".join([f"{key}: {value}" for key, value in cleaned_company_info.items()])

        # 不要な文字の削除
        cleaned_mission_text = remove_unnecessary_characters(mission_text)
        cleaned_values_text = remove_unnecessary_characters(values_text)
        # 結果の返却
        return cleaned_mission_text, cleaned_values_text, formatted_company_info


        # Fallback if information is insufficient
        if 'Not Found' in cleaned_mission_text or 'Not Found' in cleaned_values_text:
            return scrape_default(job_url)  # Fallback function to be defined separately

        logging.info("Successfully scraped Wantedly job posting")
        return cleaned_mission_text, cleaned_values_text

    except Exception as e:
        logging.error(f"Error occurred while scraping: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()

def scrape_wantedly_story(job_url):
    driver = initialize_driver()  # Assuming initialize_driver() sets up the Selenium WebDriver


    try:
        logging.info(f"Starting scraping Wantedly job posting at {job_url}")
        driver.get(job_url)
        WebDriverWait(driver, 60).until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        wait = WebDriverWait(driver, 60)
        element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.article-title")))

        outer_html = driver.execute_script("return document.documentElement.outerHTML")
        file_name = generate_file_name_from_url(job_url)
        save_html_source(outer_html, file_name, "wantedly_story")
        soup = BeautifulSoup(outer_html, 'html.parser')

        def get_section_text(soup, tag, class_name=None):
            if class_name:
                section = soup.find(tag, class_=class_name)
            else:
                section = soup.find(tag)
            if section:
                return section.get_text(strip=True)
            return "Section text not found."

        article_section = soup.find('section', class_='article-description')
        end_point = soup.find('div', class_='post-content-simple-projects')

        if article_section and end_point:
           # Extract the HTML from start to end point
           required_html = str(soup)[str(soup).find(str(article_section)):str(soup).find(str(end_point))]

           # Parse the new HTML snippet
           snippet_soup = BeautifulSoup(required_html, 'html.parser')

           sections = []
           for tag in ['h1', 'h3', 'div', 'span', 'p']:
               for element in snippet_soup.find_all(tag):
                   sections.append(element.get_text(strip=True))


        # 重複セクションの除去
        unique_sections = remove_duplicates(sections)
        # クリーニングされたテキストの生成
        cleaned_story_text = '\n'.join(unique_sections)
        # ここで必要に応じてcleaned_story_textをクリーニング
        cleaned_story_text = remove_unnecessary_characters(cleaned_story_text)

        logging.info("Successfully scraped Wantedly job posting")
        return cleaned_story_text

        # 情報が不足している場合のフォールバック処理（必要に応じて）
        if 'Not Found' in cleaned_story_text:
            return scrape_default(job_url)  # Fallback function to be defined separately

        logging.info("Successfully scraped Wantedly job posting")
        return cleaned_story_text

    except Exception as e:
        logging.error(f"Error occurred while scraping: {e}")
        return {"error": str(e)}
    finally:
        driver.quit()
