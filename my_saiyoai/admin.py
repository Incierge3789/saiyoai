from django.contrib import admin
from .models import CustomUser, Company, ImprovementSuggestion, JobPosting
from .models import Material, Listening




# ImprovementSuggestionをJobPosting管理画面にインラインで表示するためのクラス
class ImprovementSuggestionInline(admin.StackedInline):
    model = ImprovementSuggestion
    extra = 1  # 新規で追加するImprovementSuggestionの数

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'job_url', 'job_title', 'last_updated']
    inlines = [ImprovementSuggestionInline]  # JobPosting管理画面にインライン表示する


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_staff']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'culture_url', 'job_url')

@admin.register(ImprovementSuggestion)
class ImprovementSuggestionAdmin(admin.ModelAdmin):
    list_display = ['job_url', 'culture_url', 'job_ticket_suggestion', 'scout_text_suggestion', 'story_suggestion', 'job_posting']
    #list_select_related = ['job_posting']


admin.site.register(Material)
admin.site.register(Listening)

