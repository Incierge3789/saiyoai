# my_saiyoai/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Company
from django import forms
from .models import CustomUser
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, URLValidator
import re
from django.utils.crypto import get_random_string
import logging
from .models import Material


logger = logging.getLogger(__name__)

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email',)
        help_texts = {
            'email': 'ご登録に使用されるメールアドレスです。ログイン時にも使用します。',
            'password1': 'パスワードは最低8文字必要です。英数字を組み合わせるとより安全です。',
            'password2': 'セキュリティを確保するため、もう一度パスワードを入力してください。',
        }

    def generate_unique_username(self, email):
        base_username = email.split('@')[0]
        while True:
            username = base_username + get_random_string(5)
            if not CustomUser.objects.filter(username=username).exists():
                return username

    def save(self, commit=True):
        try:
            user = super().save(commit=False)
            user.username = self.generate_unique_username(self.cleaned_data['email'])
            if commit:
                user.save()
            return user
        except Exception as e:
            logger.error(f"Error in CustomUserCreationForm: {e}")
            raise

class CompanyForm(forms.ModelForm):
    culture_url = forms.URLField(required=True, help_text='企業の文化や価値観を紹介するページのURLを入力してください。')
    job_url = forms.URLField(required=False, help_text='採用情報のページのURLを入力してください（任意）。')

    class Meta:
        model = Company
        fields = ['name', 'phone', 'culture_url', 'job_url']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': '例：株式会社サンプル'}),
            'phone': forms.TextInput(attrs={'required': 'True', 'placeholder': '+81-3-1234-5678'}),
            'culture_url': forms.URLInput(attrs={'placeholder': 'https://www.example.com/culture'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not re.match(r'^\d+$', phone):
            raise ValidationError("有効な電話番号を入力してください。")
        return phone

    def clean_culture_url(self):
        culture_url = self.cleaned_data['culture_url']
        validate_url = URLValidator()
        try:
            validate_url(culture_url)
        except ValidationError:
            raise ValidationError("有効なURLを入力してください。")
        return culture_url

class EditProfileForm(forms.ModelForm):
    # CustomUser モデルのフィールド
    email = forms.EmailField(required=True, label='メールアドレス')

    # Company モデルのフィールド
    company_name = forms.CharField(max_length=255, required=True, label='会社名')
    company_email = forms.EmailField(required=True, label='会社メール')
    company_phone = forms.CharField(max_length=20, required=True, label='会社の電話番号')
    company_culture_url = forms.URLField(required=True, label='企業文化のURL')
    company_job_url = forms.URLField(required=True, label='求人情報のURL')

    class Meta:
        model = CustomUser
        fields = ['email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            # Company インスタンスの更新
            company, created = Company.objects.get_or_create(user=user)
            company.name = self.cleaned_data['company_name']
            company.email = self.cleaned_data['company_email']
            company.phone = self.cleaned_data['company_phone']
            company.culture_url = self.cleaned_data['company_culture_url']
            company.job_url = self.cleaned_data['company_job_url']
            company.save()

        return user


class StyleApplicationForm(forms.Form):
    item_type = forms.ChoiceField(choices=[('job_ticket', '求人票'), ('scout_text', 'スカウトメール'), ('story', 'ストーリー')], label='改善項目')
    style = forms.ChoiceField(choices=[
        ('casual', 'カジュアル'), 
        ('formal', 'フォーマル'),
        ('innovative', 'イノベーティブ'),
        ('creative', 'クリエイティブ')
    ], label='スタイル')
    # その他必要なフィールド


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['title', 'description', 'file']  # 'file' はアップロードする教材ファイルのフィールド


class QuestionForm(forms.Form):
    question = forms.CharField(label='あなたの質問', max_length=1000)
