# main/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView 
from django.http import JsonResponse  
from main.views import (
    scan_barcode, advanced_cross_insights, google_auth,
    trigger_notifications, generate_notifications_now,
    push_subscribe,
    # ✅ أضف هذه الدوال الجديدة
    manage_profile, change_password, delete_my_account,
    export_all_data, backup_data, restore_backup,
    user_settings, manage_goals,
    # ✅ أضف دوال الإشعارات الجديدة
    create_notification, get_notifications,
    mark_notification_read, mark_all_notifications_read,
    delete_notification, delete_all_read_notifications
)
from main import views

# =========================================================
# ✅ إنشاء الـ Router (مرة واحدة فقط لكل ViewSet)
# =========================================================
router = DefaultRouter()
router.register(r'activities', views.PhysicalActivityViewSet, basename='activities')
router.register(r'sleep', views.SleepViewSet, basename='sleep')
router.register(r'mood-logs', views.MoodEntryViewSet, basename='mood') 
router.register(r'health_status', views.HealthStatusViewSet, basename='health_status')
router.register(r'meals', views.MealViewSet, basename='meals')
router.register(r'food-items', views.FoodItemViewSet, basename='food-items')
router.register(r'habit-definitions', views.HabitDefinitionViewSet, basename='habit-definitions')
router.register(r'habit-logs', views.HabitLogViewSet, basename='habit-logs')
router.register(r'goals', views.HealthGoalViewSet, basename='goals')
router.register(r'conditions', views.ChronicConditionViewSet, basename='conditions')
router.register(r'medical-records', views.MedicalRecordViewSet, basename='medical-records')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendations')
router.register(r'chat-logs', views.ChatLogViewSet, basename='chat-logs')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')
router.register(r'environment-data', views.EnvironmentDataViewSet, basename='environment-data')
router.register(r'users', views.UserProfileViewSet, basename='users')


# =========================================================
# ✅ المسارات الأساسية
# =========================================================
base_urls = [
    # ✅ مسار تجديد التوكن
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ✅ مسار التحليلات المتقدمة
    path('advanced-insights/', advanced_cross_insights, name='advanced-insights'),
    
    # 🌤️ الطقس
    path('weather/', views.get_weather, name='weather'),
    
    # 🥗 التغذية والبحث عن الطعام
    path('food/search/', views.search_food, name='food-search'),
    
    # 💪 التمارين الرياضية
    path('exercises/suggest/', views.suggest_exercises, name='exercise-suggest'),
    
    # 😊 تحليل المشاعر
    path('sentiment/analyze/', views.analyze_sentiment, name='sentiment-analyze'),
    
    # 💡 التوصيات الذكية
    path('smart-recommendations/', views.get_smart_recommendations, name='smart-recommendations'),
    
    # 🧠 تحليلات ذكية متكاملة
    path('analytics/smart-insights/', views.smart_insights, name='smart-insights'),
    path('cross-insights/', views.cross_insights, name='cross-insights'),
    
    # 📊 التقارير
    path('reports/all-data/', views.get_all_reports_data, name='reports-all-data'),
    
    # ✅ مسار الاختبار
    path('test-simple/', lambda request: JsonResponse({'status': 'ok', 'message': 'Test endpoint works!'})),
    
    # ✅ ماسح الباركود
    path('scan-barcode/', scan_barcode, name='scan-barcode'),
    
    # ⌚ بيانات الساعة الذكية
    path('watch/health-data/', views.watch_health_data, name='watch_health_data'),
    path('watch/history/', views.watch_history, name='watch_history'),
    path('watch/adb-data/', views.adb_watch_data, name='adb_watch_data'),
    
    # 🩺 الأدوية
    path('medications/search/', views.search_medication, name='search-medication'),
    path('medications/<int:medication_id>/', views.get_medication_details, name='medication-details'),
    path('medications/user/', views.get_user_medications, name='user-medications'),
    path('medications/user/add/', views.add_user_medication, name='add-user-medication'),
    path('medications/user/<int:user_med_id>/delete/', views.delete_user_medication, name='delete-user-medication'),
    
    # ✅ Google Auth
    path('auth/google/', google_auth, name='google_auth'),
    
    # ✅ مسار Push Notifications الأساسي
    path('push-subscribe/', push_subscribe, name='push-subscribe'),
    path('achievements/', views.get_user_achievements, name='achievements'),
    
    # ✅ إدارة الحساب (هذه المسارات الجديدة)
    path('profile/', manage_profile, name='manage_profile'),
    path('change-password/', change_password, name='change_password'),
    path('delete-account/', delete_my_account, name='delete_account'),
    path('export-data/', export_all_data, name='export_data'),
    path('backup/', backup_data, name='backup_data'),
    path('restore/', restore_backup, name='restore_backup'),
    path('settings/', user_settings, name='user_settings'),
    path('goals/', manage_goals, name='manage_goals'),
    
    # ✅ إشعارات داخل التطبيق (المسارات الجديدة)
    path('notifications/create/', create_notification, name='create-notification'),
    path('notifications/get/', get_notifications, name='get-notifications'),
    path('notifications/<int:notification_id>/mark-read/', mark_notification_read, name='mark-notification-read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark-all-notifications-read'),
    path('notifications/<int:notification_id>/delete/', delete_notification, name='delete-notification'),
    path('notifications/delete-all-read/', delete_all_read_notifications, name='delete-all-read-notifications'),
    path('notifications/create/', views.create_notification, name='create-notification'),
]


# =========================================================
# ✅ مسارات الإشعارات المخصصة (لأن الـ router لا يولدها تلقائياً)
# =========================================================
notification_custom_urls = [
    path('notifications/unread-count/', 
         views.NotificationViewSet.as_view({'get': 'unread_count'}), 
         name='notification-unread-count'),
    
    path('notifications/stats/', 
         views.NotificationViewSet.as_view({'get': 'stats'}), 
         name='notification-stats'),
    
    path('notifications/recent/', 
         views.NotificationViewSet.as_view({'get': 'recent'}), 
         name='notification-recent'),
    
    path('notifications/mark-all-read/', 
         views.NotificationViewSet.as_view({'post': 'mark_all_read'}), 
         name='notification-mark-all-read'),
    
    path('notifications/delete-all-read/', 
         views.NotificationViewSet.as_view({'delete': 'delete_all_read'}), 
         name='notification-delete-all-read'),
    
    path('notifications/archive/', 
         views.NotificationViewSet.as_view({'get': 'archive', 'post': 'restore_from_archive'}), 
         name='notification-archive'),
    
    path('notifications/generate-auto/', 
         views.NotificationViewSet.as_view({'post': 'generate_auto'}), 
         name='notification-generate-auto'),
    
    path('notifications/save-push-subscription/', 
         views.NotificationViewSet.as_view({'post': 'save_push_subscription'}), 
         name='save-push-subscription'),
    
    path('notifications/send-push/', 
         views.NotificationViewSet.as_view({'post': 'send_push'}), 
         name='send-push'),
]


# =========================================================
# ✅ مسارات الإشعارات المجدولة (Cron)
# =========================================================
cron_urls = [
    path('generate-notifications/', generate_notifications_now, name='generate-notifications'),
    path('trigger-notifications/', trigger_notifications, name='trigger-notifications'),
]


# =========================================================
# ✅ دمج جميع المسارات
# =========================================================
urlpatterns = [
    # ✅ مسارات الـ Router (تشمل /notifications/ العادي)
    path('', include(router.urls)),
    
    # ✅ مسارات الإشعارات المخصصة
    *notification_custom_urls,
    
    # ✅ مسارات الإشعارات المجدولة
    *cron_urls,
    
    # ✅ المسارات الأساسية
    *base_urls,
]