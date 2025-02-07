# models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth import get_user_model

class CustomUser(AbstractUser):
    # カスタムユーザーモデル、会社関連のフィールドは削除
    pass

class Company(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    culture_url = models.URLField()
    job_url = models.URLField()

    def __str__(self):
        return self.name


class UserAccount(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)

def get_default_user():
    User = get_user_model()
    try:
        default_user = User.objects.get(username='default_username')
    except User.DoesNotExist:
        default_user = User.objects.create_user(username='default_username', password='default_password')
    return default_user.id  # ユーザーIDを返す


# ImprovementSuggestion モデル
class ImprovementSuggestion(models.Model):
    job_url = models.CharField(max_length=500)
    culture_url = models.CharField(max_length=500)
    job_ticket_suggestion = models.TextField()
    scout_text_suggestion = models.TextField()
    story_suggestion = models.TextField()
    job_posting = models.ForeignKey(
        'JobPosting',
        on_delete=models.CASCADE,
        related_name='improvement_suggestions',  # 変更: 複数形の名前にして関連づける
        null=True,
        blank=True
    )
    # 新しいフィールド
    styled_job_ticket_suggestion = models.TextField(null=True, blank=True)
    styled_scout_text_suggestion = models.TextField(null=True, blank=True)
    styled_story_suggestion = models.TextField(null=True, blank=True)
    word_limit = models.IntegerField(default=500)  # デフォルトは500とします
    user_feedback = models.TextField(null=True, blank=True)  # 新しく追加するフィールド
    dall_e_image_url = models.URLField(null=True, blank=True)  # DALL-Eで生成された画像のURLを保存する新しいフィールド
    #削除model
    is_deleted = models.BooleanField(default=False)
    edited_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # 新しいフィールドを追加
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')


# JobPosting モデル
class JobPosting(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        default=get_default_user
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    job_url = models.URLField()
    job_title = models.CharField(max_length=200)
    job_description = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)  # 追加するフィールド
    # improvement_suggestion の OneToOneField 定義を削除


#aiskills
class Material(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='materials/')

class Listening(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    listened_on = models.DateTimeField(auto_now_add=True)

class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
