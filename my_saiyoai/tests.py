from django.test import TestCase, Client
from my_saiyoai.models import ImprovementSuggestion
from django.contrib.auth import get_user_model  # カスタムユーザーモデルを取得

CustomUser = get_user_model()  # カスタムユーザーモデルを取得

class DashboardTestCase(TestCase):
    def setUp(self):
        # カスタムユーザーモデルを使用してユーザーを作成
        self.user = CustomUser.objects.create_user(username='testuser', password='testpassword')


class DashboardTestCase(TestCase):
    def test_dashboard_with_suggestion(self):
        # ImprovementSuggestion オブジェクトを作成
        suggestion = ImprovementSuggestion.objects.create(
            job_ticket_suggestion="Some suggestion",
            scout_text_suggestion="Some text",
            story_suggestion="Some story"
        )
        
        # ダッシュボードを呼び出し、レスポンスを取得
        response = self.client.get('/dashboard/')
        
        # レスポンスのステータスコードを確認
        self.assertEqual(response.status_code, 200)
        
        # レスポンスのコンテキストデータを確認
        self.assertEqual(response.context['job_ticket_suggestion'], "Some suggestion")
        self.assertEqual(response.context['scout_text_suggestion'], "Some text")
        self.assertEqual(response.context['story_suggestion'], "Some story")

    def test_dashboard_without_suggestion(self):
        # ImprovementSuggestion オブジェクトを作成しない場合のテスト
        response = self.client.get('/dashboard/')
        
        # レスポンスのステータスコードを確認
        self.assertEqual(response.status_code, 200)
        
        # レスポンスのコンテキストデータを確認
        self.assertEqual(response.context.get('job_ticket_suggestion'), None)
        self.assertEqual(response.context.get('scout_text_suggestion'), None)
        self.assertEqual(response.context.get('story_suggestion'), None)
