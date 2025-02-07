# wantedly_scraper.py
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

class WantedlyScraper(BaseScraper):
    
    def scrape_wantedly_company(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
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
            cleaned_company_info = {key: self.remove_unnecessary_characters(value) for key, value in company_info.items()}

            # 辞書の内容を文字列として整形
            formatted_company_info = "\n".join([f"{key}: {value}" for key, value in cleaned_company_info.items()])

            # 不要な文字の削除
            cleaned_mission_text = self.remove_unnecessary_characters(mission_text)
            cleaned_values_text = self.remove_unnecessary_characters(values_text)
            # 結果の返却
            return cleaned_mission_text, cleaned_values_text, formatted_company_info

        except Exception as e:
            logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
            raise
        finally:
            self.quit_driver()

    def scrape_wantedly_story(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            outer_html = self.driver.execute_script("return document.documentElement.outerHTML")
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
            unique_sections = self.remove_duplicates(sections)
            # クリーニングされたテキストの生成
            cleaned_story_text = '\n'.join(unique_sections)
            # ここで必要に応じてcleaned_story_textをクリーニング
            cleaned_story_text = self.remove_unnecessary_characters(cleaned_story_text)

            return cleaned_story_text

        except Exception as e:
            logger.error(f"Error occurred while scraping {url}: {str(e)}", exc_info=True)
            raise
        finally:
            self.quit_driver()
