# main/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """إنشاء ملف تعريف للمستخدم عند إنشاء حساب جديد"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """حفظ ملف تعريف المستخدم عند حفظ المستخدم"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


# ==============================================================================
# ✅ API endpoint لتحديث اللغة من frontend
# ==============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_language(request):
    """
    تحديث لغة المستخدم من frontend
    """
    lang = request.data.get('lang', 'ar')
    
    # التحقق من صحة اللغة
    if lang not in ['ar', 'en']:
        return Response({
            'success': False,
            'error': 'اللغة غير مدعومة. استخدم ar أو en' if request.data.get('lang') == 'ar' else 'Language not supported. Use ar or en'
        }, status=400)
    
    # ✅ تخزين اللغة في profile
    if hasattr(request.user, 'profile'):
        request.user.profile.language = lang
        request.user.profile.save()
    
    # ✅ تخزين في session كنسخة احتياطية
    request.session['app_lang'] = lang
    
    # ✅ تحديث لغة المستخدم في نموذج المستخدم إذا كان الحقل موجوداً
    if hasattr(request.user, 'language'):
        request.user.language = lang
        request.user.save()
    
    return Response({
        'success': True,
        'message': 'تم تحديث اللغة بنجاح' if lang == 'ar' else 'Language updated successfully',
        'language': lang
    })


# ==============================================================================
# ✅ API endpoint لجلب لغة المستخدم الحالية
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_language(request):
    """
    جلب لغة المستخدم الحالية
    """
    # محاولة جلب من profile
    user_lang = 'ar'
    if hasattr(request.user, 'profile') and request.user.profile.language:
        user_lang = request.user.profile.language
    elif hasattr(request.user, 'language') and request.user.language:
        user_lang = request.user.language
    elif request.session.get('app_lang'):
        user_lang = request.session.get('app_lang')
    
    return Response({
        'success': True,
        'language': user_lang,
        'is_arabic': user_lang == 'ar'
    })