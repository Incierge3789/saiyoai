# my_saiyoai/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import UserAccount, JobPosting
from django.http import HttpResponse
from .tasks import add, process_result  # tasks.pyから関数をインポート
from .utils import clean_text
from .forms import CustomUserCreationForm
from .models import Company, UserAccount, ImprovementSuggestion
from django.contrib.auth import authenticate, login
from django.db.models.functions import TruncDate
from django.db.models import Count
from collections import defaultdict
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import openai
import os
import re
import logging
from typing import Dict
import time
import cProfile
from openai.error import OpenAIError
from django.db import DatabaseError
import json
from .session_manager import SessionManager
from .prompts import generate_job_ticket_prompt, generate_scout_text_prompt, generate_story_prompt
from .prompts import generate_chatbot_prompt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import EditProfileForm
from django.shortcuts import render, redirect, get_object_or_404
from .forms import EditProfileForm
from django.db import transaction
from .forms import CustomUserCreationForm, CompanyForm  # CompanyForm を追加
from .models import ImprovementSuggestion, CustomUser
import tiktoken
from .prompts import generate_styled_job_ticket_prompt, generate_styled_scout_text_prompt, generate_styled_story_prompt
from .utils import generate_image_via_api
from django.views.decorators.csrf import csrf_exempt
from .models import Material
from .forms import MaterialForm
from .forms import QuestionForm
from .utils import get_gpt_response
from .models import Conversation
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from dotenv import load_dotenv
from .scrapers.base_scraper import BaseScraper
from .scrapers.doda_scraper import DodaScraper
from .scrapers.entenshoku_scraper import EntenshokuScraper
from .scrapers.indeed_scraper import IndeedScraper
from .scrapers.mynavi_scraper import MynaviScraper
from .scrapers.rikunavi_scraper import RikunaviScraper
from .scrapers.wantedly_scraper import WantedlyScraper

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv('OPENAI_KEY')
logger.info(f"OpenAI API Key is set: {'OPENAI_KEY' in os.environ}")

# GPT-4のトークン化エンコーダーを初期化
tokenizer = tiktoken.encoding_for_model("gpt-4")

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == "POST":
        user_form = CustomUserCreationForm(request.POST)
        company_form = CompanyForm(request.POST)

        if user_form.is_valid() and company_form.is_valid():
            user = user_form.save()

            # CompanyForm で提供された情報を使って Company インスタンスを作成
            company = company_form.save(commit=False)
            company.user = user
            company.save()

            # JobPosting インスタンスのデフォルト値を設定
            job_posting = JobPosting(
                user=user,
                company=company,
                job_title="デフォルト職種",
                job_url=company.job_url if company.job_url else "http://example.com/job",  # company_formで提供されたURLを使用
                job_description="デフォルトの職務内容"
            )
            job_posting.save()

            # ImprovementSuggestion インスタンスのデフォルト値を設定
            improvement_suggestion = ImprovementSuggestion(
                job_url=job_posting.job_url,
                culture_url=company.culture_url,
                job_ticket_suggestion="デフォルトの求人票提案",
                scout_text_suggestion="デフォルトのスカウト文面提案",
                story_suggestion="デフォルトのストーリー提案",
                job_posting=job_posting
            )
            improvement_suggestion.save()

            # ユーザーをログインさせる際に使用する認証バックエンドを指定
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            return redirect('my_saiyoai:index')
    else:
        user_form = CustomUserCreationForm()
        company_form = CompanyForm()

    return render(request, 'register.html', {'user_form': user_form, 'company_form': company_form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # ユーザーがログインした後にダッシュにリダイレクト
            return redirect('my_saiyoai:dashboard')  # ここを変更
        else:
            # ログイン失敗時のエラーメッセージ
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def calculate_max_tokens(user_requested_chars):
    # 日本語の文字をトークンに変換（1文字あたり4トークンと仮定）
    if user_requested_chars == 500:
        return 2000
    elif user_requested_chars == 1000:
        return 4000
    elif user_requested_chars == 1500:
        return 6000
    else:
        return 2000  # デフォルト値

# get_completion 関数の変更
def get_completion(prompt, user_requested_chars, model="gpt-4"):
    max_tokens = calculate_max_tokens(user_requested_chars)

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        logger.error(f"Error in get_completion: {str(e)}")
        return ""


def generate_improvement_suggestions(text: str):
    # プロンプトの生成
    job_ticket_prompt = generate_job_ticket_prompt(text)
    scout_text_prompt = generate_scout_text_prompt(text)
    story_prompt = generate_story_prompt(text)

    # API呼び出し
    logger.debug("Making API call for job_ticket_suggestion...")
    job_ticket_suggestion = get_completion(job_ticket_prompt)
    logger.debug(f"Received job_ticket_suggestion: {job_ticket_suggestion}")

    logger.debug("Making API call for scout_text_suggestion...")
    scout_text_suggestion = get_completion(scout_text_prompt)
    logger.debug(f"Received scout_text_suggestion: {scout_text_suggestion}")

    logger.debug("Making API call for story_suggestion...")
    story_suggestion = get_completion(story_prompt)
    logger.debug(f"Received story_suggestion: {story_suggestion}")

    # ログの出力
    logger.info("===== Job Ticket Suggestion =====")
    logger.info(job_ticket_suggestion)
    logger.info("===== Scout Text Suggestion =====")
    logger.info(scout_text_suggestion)
    logger.info("===== Story Suggestion =====")
    logger.info(story_suggestion)

    return {
        "job_ticket": job_ticket_suggestion,
        "scout_text": scout_text_suggestion,
        "story": story_suggestion
    }




def parse_improvement_suggestions(text):
    logger.debug("改善提案の解析を開始")

    # context辞書の初期化
    context = {"job_ticket": {}, "scout_text": [], "story": []}

    # 各項目を抽出するための正規表現パターン
    patterns = {
        "企業名": r"企業名:\n・(.+?)\n",
        "会社概要": r"会社概要:\n・(.+?)\n\n",
        "募集職種": r"募集職種:\n・(.+?)\n\n",
        "仕事内容": r"仕事内容:\n・(.+?)\n\n",
        "募集要項": r"募集要項:\n(・.+?)\n\n",
        "応募資格": r"応募資格:\n・(.+?)\n\n",
        "福利厚生": r"福利厚生:\n・(.+?)\n\n",
        "応募方法": r"応募方法:\n・(.+?)\n\n",
        "会社情報": r"会社情報:\n(・.+?)\n\n",
        "選考プロセス": r"選考プロセス:\n・(.+?)\n"
    }

    # テキストから各項目を抽出してコンテキストに追加
    for key, pattern in patterns.items():
        logger.debug(f"{key}を検索中")
        match = re.search(pattern, text, re.DOTALL)
        if match:
            context["job_ticket"][key] = match.group(1).strip().replace('\n', ' ')
            logger.debug(f"{key}を発見: {context['job_ticket'][key]}")
        else:
            logger.warning(f"{key}が見つかりません")

    # スカウトとストーリーのセクションを題名と本文に分けて抽出する正規表現
    scout_story_pattern = r"題名:\s*(.*?)\n本文:\s*(.*?)(?=\n題名:|$)"
    logger.debug("スカウトとストーリーのセクションを抽出中")

    # テキストからスカウトとストーリーセクションを抽出
    matches = re.findall(scout_story_pattern, text, re.DOTALL)

    # 抽出されたマッチを処理
    if matches:
        # 最初のマッチをスカウトセクションとして処理
        title, text = matches[0]
        context['scout_text'].append({'title': title.strip(), 'text': text.strip()})
        logger.debug(f"スカウトセクションを追加しました: タイトル='{title.strip()}'")

        # 2番目のマッチが存在する場合、それをストーリーセクションとして処理
        if len(matches) > 1:
            title, text = matches[1]
            context['story'].append({'title': title.strip(), 'text': text.strip()})
            logger.debug(f"ストーリーセクションを追加しました: タイトル='{title.strip()}'")

    logger.debug("改善提案の解析を完了しました")
    return context


def convert_to_html(text):
    """Convert \n in text to <br /> for HTML display."""
    return text.replace('\n', '<br />')

def estimate_tokens(text, tokenizer):
    tokens = tokenizer.encode(text)
    return len(tokens)

def trim_text_to_max_tokens(text, max_tokens, tokenizer):
    tokens = tokenizer.encode(text)
    if len(tokens) > max_tokens:
        trimmed_tokens = tokens[:max_tokens]
        return tokenizer.decode(trimmed_tokens)
    else:
        return text


def parse_suggestion_details(suggestion_text):
    parts = suggestion_text.split('\n')
    suggestion_dict = {}
    current_key = None
    default_key_count = 0

    for part in parts:
        part = part.strip()
        if part:
            if ':' in part:  # キーと値のペアの場合
                key, value = [x.strip() for x in part.split(':', 1)]
                current_key = key
                suggestion_dict[current_key] = value
            else:  # 値のみの場合
                if current_key is None:
                    current_key = f"Default Key {default_key_count}"
                    default_key_count += 1
                if current_key in suggestion_dict:
                    suggestion_dict[current_key] += '\n' + part
                else:
                    suggestion_dict[current_key] = part

    return suggestion_dict


def analyze(request):
    session_manager = SessionManager()

    try:
        job_url = request.POST.get('job_url', None)
        culture_url = request.POST.get('culture_url', None)
        job_scrape_method = request.POST.get('job_scrape_method', 'default')
        culture_scrape_method = request.POST.get('culture_scrape_method', 'default')

        # word_limit の取得と検証
        word_limit_str = request.POST.get('word_limit')
        if word_limit_str is not None:
            word_limit = int(word_limit_str)
        else:
            word_limit = 500  # デフォルト値
        
        logger.info(f"Word limit: {word_limit}")  # word_limit の値をログに出力

        # 入力の存在と型を確認
        if job_url and not isinstance(job_url, str):
            logger.error("Job URL is invalid.")
            return render(request, 'error.html', {'error': 'Job URL is invalid.'})

        if culture_url and not isinstance(culture_url, str):
            logger.error("Culture URL is invalid.")
            return render(request, 'error.html', {'error': 'Culture URL is invalid.'})

        # 変数の初期化
        job_scrape_result = ""
        culture_scrape_result = ""

        # 両方のURLが無効または提供されていない場合
        if not job_url and not culture_url:
            logger.error("Both Job URL and Culture URL are missing or invalid.")
            return render(request, 'error.html', {'error': 'Both Job URL and Culture URL are missing or invalid. Please provide at least one URL.'})

        # 求人ページのスクレイピング
        if job_url:
            if job_scrape_method == 'doda':
                scraper = DodaScraper()
                job_scrape_result = scraper.scrape_doda(job_url)
            elif job_scrape_method == 'entenshoku':
                scraper = EntenshokuScraper()
                job_scrape_result = scraper.scrape_entenshoku(job_url)
            elif job_scrape_method == 'indeed':
                scraper = IndeedScraper()
                job_scrape_result = scraper.scrape_indeed(job_url)
            elif job_scrape_method == 'mynavi':
                scraper = MynaviScraper()
                job_scrape_result = scraper.scrape_mynavi(job_url)
            elif job_scrape_method == 'rikunavi':
                scraper = RikunaviScraper()
                job_scrape_result = scraper.scrape_rikunavi(job_url)
            elif job_scrape_method == 'wantedly':
                scraper = WantedlyScraper()
                job_scrape_result = scraper.scrape_wantedly_story(job_url)
            else:
                scraper = BaseScraper()
                job_scrape_result = scraper.scrape_default(job_url)

            # スクレイピング結果をログ出力
            logger.debug(f"Scraped job page: {job_scrape_result}")

            # 返り値が文字列型であるかを確認
            if not isinstance(job_scrape_result, str):
                logger.error("Scraping function did not return a string.")
                return render(request, 'error.html', {'error': 'Scraping function error.'})

            # エラーが返された場合の処理
            if "error" in job_scrape_result:
                logger.error(f"Scraping error: {job_scrape_result['error']}")
                return render(request, 'error.html', {'error': job_scrape_result['error']})

        # 企業理念・文化ページのスクレイピング
        if culture_url:
            if culture_scrape_method == 'wantedly_company':
                scraper = WantedlyScraper()
                culture_scrape_result = scraper.scrape_wantedly_company(culture_url)
            elif culture_scrape_method == 'wantedly_story':
                scraper = WantedlyScraper()
                culture_scrape_result = scraper.scrape_wantedly_story(culture_url)  # 新しいスクレイピング関数を追加

                # エラーが返された場合の処理
                if isinstance(culture_scrape_result, dict) and "error" in culture_scrape_result:
                    error_message = culture_scrape_result.get("error", "Unknown error")
                    logger.error(f"Error during scraping Wantedly: {error_message}")
                    return render(request, 'error.html', {'error': error_message})
            else:  # デフォルトスクレイピング
                scraper = BaseScraper()
                culture_scrape_result = scraper.scrape_default(culture_url)
                # 戻り値の型チェック（scrape_default の場合も同様にチェックを行う）
                if not isinstance(culture_scrape_result, str):
                    logger.error("Error during default scraping")
                    return render(request, 'error.html', {'error': 'Default scraping failed.'})

            # 文化ページのスクレイピング結果をログ出力
            logger.debug(f"Scraped culture page: {culture_scrape_result}")

        # スクレイピングした結果が文字列でない場合は文字列に変換
        cleaned_job_text = str(job_scrape_result) if job_scrape_result else ""
        cleaned_culture_text = str(culture_scrape_result) if culture_scrape_result else ""

        # スクレイピングした結果を3500文字にトリミング
        cleaned_job_text = cleaned_job_text[:3500]
        cleaned_culture_text = cleaned_culture_text[:3500]

        # トリミングしたテキストの長さをデバッグログに出力
        logger.debug(f"Cleaned job text length: {len(cleaned_job_text)}")
        logger.debug(f"Cleaned culture text length: {len(cleaned_culture_text)}")

        # 正規表現による情報抽出関数の定義
        def extract_info_with_regex(text, patterns):
            extracted_info = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, text)
                extracted_info[key] = match.group(1) if match else "情報なし"
            return extracted_info

        # 求人情報のキーワードに基づいた正規表現パターン
        job_patterns = {
            '企業名': r'企業名\s*:\s*(.+)',
            '職種': r'職種\s*:\s*(.+)',
            '仕事内容': r'仕事内容\s*:\s*(.+)',
            '応募資格': r'応募資格\s*:\s*(.+)',
            '勤務地': r'勤務地\s*:\s*(.+)',
            '給与': r'給与\s*:\s*(.+)',
            '勤務時間': r'勤務時間\s*:\s*(.+)',
            '雇用形態': r'雇用形態\s*:\s*(.+)',
            '福利厚生': r'福利厚生\s*:\s*(.+)',
            '選考プロセス': r'選考プロセス\s*:\s*(.+)'
        }

        # 企業文化情報のキーワードに基づいた正規表現パターン
        culture_patterns = {
            '企業理念': r'企業理念\s*:\s*(.+)',
            'ビジョン': r'ビジョン\s*:\s*(.+)',
            'ミッション': r'ミッション\s*:\s*(.+)',
            'コアバリュー': r'コアバリュー\s*:\s*(.+)',
            '社内文化': r'社内文化\s*:\s*(.+)',
            'チームワーク': r'チームワーク\s*:\s*(.+)',
            '社員の声': r'社員の声\s*:\s*(.+)',
            '環境': r'環境\s*:\s*(.+)',
            'コミュニティ': r'コミュニティ\s*:\s*(.+)'
        }
        
        最小キーワード数_求人 = 7
        最小キーワード数_文化 = 5
        # 求人情報の抽出
        job_info = extract_info_with_regex(cleaned_job_text, job_patterns)
        if len(job_info) < 最小キーワード数_求人:
            job_info["全体テキスト"] = scrape_default(job_url)

        # 企業理念・文化情報の抽出
        culture_info = extract_info_with_regex(cleaned_culture_text, culture_patterns)
        if len(culture_info) < 最小キーワード数_文化:
            culture_info["全体テキスト"] = scrape_default(culture_url)

        # 抽出した情報の使用
        print(job_info)
        print(culture_info)

        # 戻り値が文字列でない場合のエラーハンドリング
        if not isinstance(cleaned_job_text, str) or not isinstance(cleaned_culture_text, str):
            logger.error("Scraped content is not a string.")
            raise TypeError("Scraped content must be a string.")
        
        
        # スクレイピングしたテキストの結合
        gpt_input_text = f"求人情報:\n{cleaned_job_text}\n\n企業文化情報:\n{cleaned_culture_text}"

        # テキストが5000文字を超える場合はトリミング
        if len(gpt_input_text) > 5000:
            gpt_input_text = gpt_input_text[:5000]

        # トークン数の推定
        estimated_tokens = estimate_tokens(gpt_input_text, tokenizer)

        # トークン数が8192を超える場合はさらにトリミング
        if estimated_tokens > 8192:
            gpt_input_text = trim_text_to_max_tokens(gpt_input_text, 8192, tokenizer)

        # APIの応答がユーザーの設定した単語上限に合うように、最大トークン数を推定
        max_tokens = int(word_limit / 4)

        # OpenAI GPT-4を使用して改善提案を生成
        try:
           logger.info("Starting generation of improvement suggestions with OpenAI GPT-4")


           # 生成するプロンプトのログ
           generated_job_ticket_prompt = generate_job_ticket_prompt(gpt_input_text, word_limit)
           generated_scout_text_prompt = generate_scout_text_prompt(gpt_input_text, word_limit)
           generated_story_prompt = generate_story_prompt(gpt_input_text, word_limit)

           logger.info(f"Generated prompt for job_ticket: {generated_job_ticket_prompt}")
           logger.info(f"Generated prompt for scout_text: {generated_scout_text_prompt}")
           logger.info(f"Generated prompt for story: {generated_story_prompt}")
           logger.info(f"Max tokens: {max_tokens}")


           # GPT-4 APIリクエスト
           logger.info("Before get_completion call for job_ticket_suggestion")
           job_ticket_suggestion = get_completion(generated_job_ticket_prompt, max_tokens)
           logger.info("After get_completion call for job_ticket_suggestion")

           logger.info("Before get_completion call for scout_text_suggestion")
           scout_text_suggestion = get_completion(generated_scout_text_prompt, max_tokens)
           logger.info("After get_completion call for scout_text_suggestion")

           logger.info("Before get_completion call for story_suggestion")
           story_suggestion = get_completion(generated_story_prompt, max_tokens)
           logger.info("After get_completion call for story_suggestion")

           # ログに生成された改善案を出力
           logger.info("Generated Job Ticket Suggestion: " + job_ticket_suggestion)
           logger.info("Generated Scout Text Suggestion: " + scout_text_suggestion)
           logger.info("Generated Story Suggestion: " + story_suggestion)

           logger.info("Finished generation of improvement suggestions with OpenAI GPT-4")
           # 生成されたテキストのトークン数をセッションマネージャに追加
           session_manager.check_session_state(len(job_ticket_suggestion) + len(scout_text_suggestion) + len(story_suggestion))

        except OpenAIError as e:
            logger.error(f"Error with OpenAI API call: {str(e)}")
            raise

        # この部分の直前にCompanyオブジェクトの取得または作成のコードを挿入
        # 現在のユーザーに紐づくCompanyオブジェクトの取得または作成
        company, created = Company.objects.get_or_create(
            user=request.user,
            defaults={
            # Companyインスタンスを作成する際のデフォルト値を設定
            'name': "デフォルト会社名",
            'phone': "000-0000-0000",
            'culture_url': "http://example.com/culture",
            'job_url': "http://example.com/job",
            }
        )
        if not created:
           # ここで必要に応じてcompanyのフィールド
           # 必要に応じてcompanyのフィールドを更新
           company.name = "更新後の会社名"
           company.phone = "更新後の電話番号"
           company.culture_url = "更新後のカルチャーURL"
           company.job_url = "更新後の求人URL"
           company.save()
        
        # この部分の直前にJobPostingオブジェクトの取得または作成のコードを挿入
        job_posting, created = JobPosting.objects.get_or_create(
            user=request.user,
            company=company, # ここでCompanyインスタンスを渡す
            job_url=job_url,
            defaults={
                'job_title': 'デフォルトの職種',  # 必要に応じてデフォルト値を設定
                'job_description': 'デフォルトの職務内容'  # 必要に応じてデフォルト値を設定
            }
        )

        # GPT-4 APIリクエストで取得した提案テキストをそのまま保存
        improvement_suggestion = ImprovementSuggestion(
            job_url=job_url,
            culture_url=culture_url,
            job_ticket_suggestion=job_ticket_suggestion,
            story_suggestion=story_suggestion,
            scout_text_suggestion=scout_text_suggestion,
            job_posting=job_posting,  # JobPostingオブジェクトを設定
        )

        # （フロントエンド表示用
        job_ticket_dict = parse_suggestion_details(job_ticket_suggestion)
        scout_text_dict = parse_suggestion_details(scout_text_suggestion)
        story_dict = parse_suggestion_details(story_suggestion)

        # 解析結果を統合して辞書に格納（フロントエンド表示用）
        suggestions = {
            'job_ticket': job_ticket_dict,
            'scout_text': scout_text_dict,
            'story': story_dict
        }

        try:
            logger.info("Before saving improvement_suggestion")
            improvement_suggestion.save()
            # セッションにImprovementSuggestionのIDを保存
            request.session['improvement_suggestion_id'] = improvement_suggestion.id
            logger.info(f"After saving improvement_suggestion with id: {improvement_suggestion.id}")
        except DatabaseError as e:
            logger.error(f"Database error while saving improvement_suggestion: {str(e)}")
            raise

    except (WebDriverException, NoSuchElementException, TimeoutException) as e:
        logger.error(f"Error occurred during web scraping: {str(e)}", exc_info=True)
        context = {
            'error_type': 'scraping_error',
            'error_message': 'ウェブサイト情報の取得中に問題が生じました。URLが正しいか、ウェブサイトがオンライン状態であることをご確認ください。問題が続く場合は、技術サポートにお問い合わせください。',
        }
        return render(request, 'error.html', context)

    except OpenAIError as e:
        logger.error(f"Error occurred with OpenAI API call: {str(e)}", exc_info=True)
        context = {
            'error_type': 'ai_error',
            'error_message': 'AIサービスの応答に問題が発生しました。システムの状態を確認して、再試行してください。引き続き問題が解決しない場合は、サポートチームまでご連絡をお願いします。',
        }
        return render(request, 'error.html', context)

    except DatabaseError as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        context = {
            'error_type': 'database_error',
            'error_message': 'データベース処理中にエラーが発生しました。データベースの接続を確認し、アクセス権限が適切であることをご確認ください。このエラーについては、システム管理者に通知されます。',
        }
        return render(request, 'error.html', context)

    except ValueError as e:
        logger.error(f"Value error: {str(e)}", exc_info=True)
        context = {
            'error_type': 'value_error',
            'error_message': '提供された情報に誤りがあります。入力内容を再確認してください。もしこのメッセージが表示され続ける場合は、サポートチームへご相談ください。',
        }
        return render(request, 'error.html', context)

    except Exception as e:  # 予期せぬその他のエラー
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        context = {
            'error_type': 'unexpected_error',
            'error_message': '予期せぬエラーが発生しました。この問題は技術部門に報告され、迅速に対応されます。ご迷惑をおかけして申し訳ありません。',
        }
        return render(request, 'error.html', context)

    except TypeError as e:
        logger.error(f"Type error: {str(e)}", exc_info=True)
        context = {
            'error_type': 'type_error',
            'error_message': 'スクレイピングした内容が文字列ではありません。URLが正しいか確認してください。',
        }
        return render(request, 'error.html', context)

    finally:
        logger.info("Completed the analyze function.")
        driver.quit()  # ドライバを終了する


    # レスポンスのコンテキストにsuggestionsを追加
    context = {
        'job_url': job_url,
        'culture_url': culture_url,
        'job_content': cleaned_job_text,
        'culture_content': cleaned_culture_text,
        'suggestions': suggestions,
        'improvement_suggestion': improvement_suggestion
    }

    return redirect('my_saiyoai:results')


def results(request):
    logger.debug("Starting results function")
    try:
        suggestion_id = request.session.get('improvement_suggestion_id')
        logger.debug(f"Suggestion ID obtained from session: {suggestion_id}")

        if suggestion_id:
            latest_suggestion = ImprovementSuggestion.objects.get(id=suggestion_id)
            logger.debug(f"Latest suggestion obtained from database: {latest_suggestion}")

            full_suggestion_text = f"{latest_suggestion.job_ticket_suggestion}\n{latest_suggestion.scout_text_suggestion}\n{latest_suggestion.story_suggestion}"
            logger.debug(f"Full suggestion text: {full_suggestion_text}")

            # parse_improvement_suggestions関数を使ってテキストを解析
            parsed_data = parse_improvement_suggestions(full_suggestion_text)

            # 解析したデータから必要な情報を取り出す
            job_ticket = parsed_data.get("job_ticket", {})
            scout_text = parsed_data.get("scout_text", {})
            story = parsed_data.get("story", {})

            context = {
                'job_url': latest_suggestion.job_url,
                'culture_url': latest_suggestion.culture_url,
                'suggestions': {
                    'job_ticket': {
                        'original': latest_suggestion.job_ticket_suggestion,
                        'styled': latest_suggestion.styled_job_ticket_suggestion
                    },
                    'scout_text': {
                        'original': latest_suggestion.scout_text_suggestion,
                        'styled': latest_suggestion.styled_scout_text_suggestion
                    },
                    'story': {
                        'original': latest_suggestion.story_suggestion,
                        'styled': latest_suggestion.styled_story_suggestion
                    },
                },
                'improvement_suggestion': latest_suggestion
            }
            logger.debug(f"Context prepared for template: {context}")

            return render(request, 'results.html', context)
        else:
            logger.debug("No improvement suggestion found in session")
            return render(request, 'error.html', {'error': 'No improvement suggestions found'})
    except ImprovementSuggestion.DoesNotExist:
        logger.error("Improvement suggestion not found in database")
        return render(request, 'error.html', {'error': 'Improvement suggestion not found'})
    finally:
        logger.debug("Completed results function")


def my_view(request):
    result = add.apply_async((10, 20), link=process_result.s())  # タスクを非同期に実行し、結果が得られたらprocess_resultを呼び出す
    return HttpResponse('Task has been executed, check for the result later.')


def style_application(request, improvement_suggestion_id):
    if request.method == 'POST':
        # リクエストからJSONデータをロード
        data = json.loads(request.body)
        item_type = data.get('item_type')
        style = data.get('style')
        logger.info(f"Style application request received for item_type={item_type}, style={style}")

        try:
            improvement_suggestion = ImprovementSuggestion.objects.get(id=improvement_suggestion_id)
            logger.info(f"ImprovementSuggestion object found with id={improvement_suggestion_id}")

            # word_limitをImprovementSuggestionインスタンスから取得
            word_limit = improvement_suggestion.word_limit
            logger.info(f"Using word_limit={word_limit} from ImprovementSuggestion for style application")

            text_to_style = getattr(improvement_suggestion, f"{item_type}_suggestion", "")
            logger.info(f"Text to style for {item_type}: {text_to_style[:100]}...")

            # item_typeに応じて適切なプロンプト生成関数を呼び出し
            if item_type == "job_ticket":
                logger.info(f"Generating prompt for job_ticket with style {style}")
                prompt = generate_job_ticket_prompt(text_to_style, style)
            elif item_type == "scout_text":
                logger.info(f"Generating prompt for scout_text with style {style}")
                prompt = generate_scout_text_prompt(text_to_style, style)
            elif item_type == "story":
                logger.info(f"Generating prompt for story with style {style}")
                prompt = generate_story_prompt(text_to_style, style)
            else:
                logger.error(f"Invalid item_type received: {item_type}")
                return JsonResponse({"error": "Invalid item type"}, status=400)

            styled_text = get_completion(prompt, word_limit * 4)  # 1単語あたり平均4文字を仮定して計算
            logger.info(f"Styled text generated for {item_type}: {styled_text}")  # スタイル適用後のテキストをログに出力

            setattr(improvement_suggestion, f"styled_{item_type}_suggestion", styled_text)
            improvement_suggestion.save()
            logger.info(f"Styled text for {item_type} saved in ImprovementSuggestion with id={improvement_suggestion_id}")

            return JsonResponse({"styled_text": styled_text}, status=200)
        except ImprovementSuggestion.DoesNotExist:
            logger.error(f"ImprovementSuggestion not found with id={improvement_suggestion_id}")
            return JsonResponse({"error": "Improvement suggestion not found"}, status=404)
    else:
        logger.warning("Invalid request method for style_application.")
        return JsonResponse({"error": "Invalid request method"}, status=405)

def select_style(request):
    logger.info("select_style function called")
    if request.method == 'POST':
        logger.info("Processing POST request in select_style")
        # JSONデータをロード
        data = json.loads(request.body)
        selected_style = data.get('selected_style')
        logger.info(f"Style selected: {selected_style}")

        if selected_style in ['casual', 'formal', 'innovative', 'creative']:
            selected_text = get_text_for_style(selected_style)
            logger.info(f"Returning text for style: {selected_style}")
            return JsonResponse({"selected_text": selected_text}, status=200)
        else:
            logger.warning(f"Invalid style selected: {selected_style}")
            return JsonResponse({"error": "Invalid style selected."}, status=400)
    else:
        logger.warning("Invalid request method for select_style")
        return JsonResponse({"error": "Invalid request method"}, status=405)

def get_text_for_style(style):
    style_text_map = {
        "casual": "This is a sample text for the Casual style.",
        "formal": "This is a sample text for the Formal style.",
        "innovative": "This is a sample text for the Innovative style.",
        "creative": "This is a sample text for the Creative style.",
    }
    return style_text_map.get(style, "Invalid style selected.")

def chatbot_view(request):
    if request.method == "POST":
        # JSONリクエストボディからユーザー入力を取得
        data = json.loads(request.body)
        user_input = data.get('user_input', '')

        # チャットボットのプロンプトを生成
        prompt = generate_chatbot_prompt(user_input)

        try:
            # GPT-4 APIを呼び出して回答を得る
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message["content"].strip()

            # 回答をJSON形式で返却
            return JsonResponse({'answer': answer}, status=200)

        except Exception as e:
            # エラー処理
            return JsonResponse({'error': str(e)}, status=500)

    # GETリクエストの場合はエラー
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def user_profile(request):
    return render(request, 'user_profile.html', {'user': request.user})


@transaction.atomic
@login_required
def edit_profile(request):
    user = request.user
    company = get_object_or_404(Company, user=user)

    if request.method == 'POST':
        user_form = EditProfileForm(request.POST, instance=user)
        company_form = CompanyForm(request.POST, instance=company)  # CompanyFormを追加
        if user_form.is_valid() and company_form.is_valid():  # 両方のフォームが有効な場合
            user_form.save()
            company_form.save()
            messages.success(request, 'プロファイルが更新されました。')
            return redirect('my_saiyoai:user_profile')
    else:
        user_form = EditProfileForm(instance=user)
        company_form = CompanyForm(instance=company)  # CompanyFormの初期化

    return render(request, 'edit_profile.html', {'user_form': user_form, 'company_form': company_form})


@login_required
def dashboard(request):
    current_user = request.user
    logger.info(f"ユーザー {current_user.username} がダッシュボードにアクセスしました。")

    job_postings = JobPosting.objects.filter(user=current_user)
    logger.info(f"ユーザー {current_user.username} の求人投稿数: {job_postings.count()}")

    if job_postings:
        logger.debug("現在のユーザーに対する求人投稿が存在します。")
    else:
        logger.debug("現在のユーザーに対する求人投稿が見つかりませんでした。")

    suggestions = ImprovementSuggestion.objects.filter(job_posting__in=job_postings).annotate(date=TruncDate('created_at')).order_by('-date')
    logger.info(f"改善提案数を取得しました: {suggestions.count()}")

    if suggestions:
        logger.debug("求人投稿に対する改善提案が存在します。")
    else:
        logger.debug("求人投稿に対する改善提案が見つかりませんでした。")

    suggestions_grouped_by_date = defaultdict(list)
    for suggestion in suggestions:
        suggestions_grouped_by_date[suggestion.date].append(suggestion)
        logger.debug(f"提案: {suggestion.id} を日付グループ: {suggestion.date} に追加しました。")

    if suggestions_grouped_by_date:
        logger.debug(f"提案が日付ごとにグループ化されました。グループ数: {len(suggestions_grouped_by_date)}")
    else:
        logger.debug("提案が日付ごとにグループ化されませんでした。")

    # suggestions_grouped_by_dateが日付キーと提案リストを値とする辞書であると仮定
    for date, suggestions in suggestions_grouped_by_date.items():
        logger.info(f"日付: {date}, 提案数: {len(suggestions)}")
        for suggestion in suggestions:
            # 提案のIDと各種提案内容をログに記録
            logger.info(f"提案ID: {suggestion.id}, 求人票提案: {suggestion.job_ticket_suggestion}")
            logger.info(f"提案ID: {suggestion.id}, スカウトテキスト提案: {suggestion.scout_text_suggestion}")
            logger.info(f"提案ID: {suggestion.id}, ストーリー提案: {suggestion.story_suggestion}")

    # 辞書への変換が成功したかを確認
    suggestions_grouped_by_dict = dict(suggestions_grouped_by_date)
    if suggestions_grouped_by_dict:
        logger.debug("日付ごとにグループ化された提案の辞書への変換が成功しました。")
    else:
        logger.debug("日付ごとにグループ化された提案の辞書への変換に失敗しました。")


    # job_postings_grouped_by_date の内容をログに記録（誤り）
    # 正しくは suggestions_grouped_by_date です
    for date, suggestions in suggestions_grouped_by_date.items():
        logger.debug(f"Date: {date}, Suggestions: {suggestions}")

    context = {
        'job_postings': job_postings,
        'suggestions_grouped_by_date': suggestions_grouped_by_dict,
    }

    logger.info(f"{current_user.username} のユーザーのためのダッシュボードをコンテキストとともにレンダリングします: {context}")
    return render(request, 'dashboard.html', context)

@csrf_exempt
def generate_image_view(request):
    if request.method == "POST":
        try:
            # JSONデータの解析
            data = json.loads(request.body)
            story_text = data.get("story_text", "")
            logger.debug(f"Received story text for image generation: {story_text}")

            # リクエストデータの詳細ログ
            logger.debug(f"Request data: {data}")

            # 画像生成処理
            image_url = generate_image_via_api(story_text)

            # API呼び出しの詳細ログは、generate_image_via_api 関数内で行う

            if image_url:
                logger.debug(f"Generated image URL: {image_url}")
                return HttpResponse(f'<img src="{image_url}" alt="Generated Image"/>')
            else:
                logger.error("Failed to generate image.")
                return HttpResponse("画像の生成に失敗しました。")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from request body.")
            return HttpResponse("Invalid JSON data.", status=400)
    else:
        logger.warning("Received a non-POST request.")
        return HttpResponse("このエンドポイントはPOSTリクエストのみを受け付けます。")


@login_required
def material_list(request):
    materials = Material.objects.all()
    return render(request, 'material_list.html', {'materials': materials})


@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material, pk=pk)
    form = QuestionForm()
    conversations = Conversation.objects.filter(user=request.user, material=material).order_by('-created_at')

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question']
            logger.info(f"User {request.user.username} asked: {question_text}")
            
            # GPT-3から回答を取得
            answer_text = get_gpt_response(material.description, question_text)
            logger.info(f"GPT-3's response: {answer_text}")

            # 会話をデータベースに保存
            Conversation.objects.create(user=request.user, material=material, question=question_text, answer=answer_text)

        else:
            logger.error(f"Invalid form submission: {form.errors}")

    return render(request, 'material_detail.html', {
        'material': material,
        'form': form,
        'conversations': conversations  # 会話履歴をテンプレートに渡す
    })


def upload_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('my_saiyoai:material_list')  # 教材リストページにリダイレクト
    else:
        form = MaterialForm()
    return render(request, 'upload_material.html', {'form': form})

@login_required
def edit_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            return redirect('my_saiyoai:material_detail', pk=material.pk)
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'edit_material.html', {'form': form})


@login_required
def delete_suggestion(request, pk):
    logger.debug(f'Delete suggestion requested for pk={pk}')
    suggestion = get_object_or_404(ImprovementSuggestion, pk=pk)
    suggestion.delete()
    logger.debug(f'Suggestion with pk={pk} deleted successfully')
    return JsonResponse({'success': True})


@csrf_protect
def edit_suggestion(request, pk):
    logger.debug(f'Edit suggestion request received for pk={pk}')

    if request.method == 'PUT':
        try:
            data = json.loads(request.body.decode('utf-8'))
            suggestion = ImprovementSuggestion.objects.get(pk=pk)

            logger.debug(f'Received edit type: {data["type"]} for pk={pk}')  # リクエストされたtypeをログに記録

            if data['type'] == 'job-ticket':
                suggestion.job_ticket_suggestion = data['text']
                logger.info(f'Updating job-ticket suggestion for pk={pk}')
            elif data['type'] == 'scout-text':
                logger.info(f'Attempting to update scout-text suggestion for pk={pk} with text: {data["text"]}')
                suggestion.scout_text_suggestion = data['text']
                logger.info(f'Updated scout-text suggestion for pk={pk}')
            elif data['type'] == 'story':
                suggestion.story_suggestion = data['text']
                logger.info(f'Updating story suggestion for pk={pk}')
            else:
                logger.error(f'Unknown type: {data["type"]} for pk={pk}')  # 不明なtypeが指定された場合のログ

            suggestion.save()
            logger.debug(f'Suggestion for pk={pk} updated successfully')
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f'Error updating suggestion for pk={pk}: {e}', exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    else:
        logger.warning(f'Invalid request method {request.method} for edit_suggestion')
        return JsonResponse({'error': 'Invalid request method'}, status=400)


def debug_request(request):
    response_data = {key: value for key, value in request.headers.items()}
    return JsonResponse(response_data)
