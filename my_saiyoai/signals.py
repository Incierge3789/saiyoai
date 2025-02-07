# my_saiyoai/signals.py
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import JobPosting, ImprovementSuggestion

@receiver(post_delete, sender=JobPosting)
def update_suggestion_status(sender, instance, **kwargs):
    suggestions = ImprovementSuggestion.objects.filter(job_posting=instance)
    for suggestion in suggestions:
        suggestion.status = 'inactive'
        suggestion.save()
