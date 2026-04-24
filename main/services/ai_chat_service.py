# main/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# يمكن إضافة API endpoint لتحديث اللغة من frontend
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_language(request):
    """تحديث لغة المستخدم من frontend"""
    lang = request.data.get('lang', 'ar')
    
    # تخزين اللغة في profile
    if hasattr(request.user, 'profile'):
        request.user.profile.language = lang
        request.user.profile.save()
    
    # تخزين في session كنسخة احتياطية
    request.session['app_lang'] = lang
    
    return Response({'success': True, 'language': lang})