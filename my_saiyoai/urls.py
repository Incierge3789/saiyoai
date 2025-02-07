from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views
from .views import dashboard
from .views import debug_request
from django.contrib.auth.views import LogoutView
from .views import generate_image_view
from .views import edit_material
from .views import (
    dashboard,
    delete_suggestion,  # 追加
    edit_suggestion,    # 追加
    generate_image_view,
    edit_material
)

app_name = 'my_saiyoai'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('analyze/', views.analyze, name='analyze'),
    path('style_application/<int:improvement_suggestion_id>/', views.style_application, name='style_application'),
    path('select_style/', views.select_style, name='select_style'), # 新しいビューへのパスを追加
    path('results/', views.results, name='results'),
    path('my_view/', views.my_view, name='my_view'),  # ここに新しいビューへのパスを追加
    path('chatbot_view', views.chatbot_view, name='chatbot_view'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('generate-image/', generate_image_view, name='generate-image'),
    path('materials/', views.material_list, name='material_list'),
    path('materials/<int:pk>/', views.material_detail, name='material_detail'),
    path('upload_material/', views.upload_material, name='upload_material'),
    path('materials/<int:pk>/edit/', edit_material, name='edit_material'),
    path('delete-suggestion/<int:pk>/', delete_suggestion, name='delete_suggestion'),
    path('edit-suggestion/<int:pk>/', edit_suggestion, name='edit_suggestion'),
    path('debug/', debug_request, name='debug_request'),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# 開発中のみメディアファイルを提供するための設定
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
