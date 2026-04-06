# main/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main import views
from rest_framework_simplejwt.views import TokenRefreshView 
from django.http import JsonResponse  
from main.views import scan_barcode, advanced_cross_insights
from main.views import google_auth  # ✅ أضف هذا السطر

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

# main/urls.py - النسخة الصحيحة

urlpatterns = [
    # ✅ مسار تجديد التوكن
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ✅ مسار التحليلات المتقدمة
    path('advanced-insights/', advanced_cross_insights, name='advanced-insights'),
    
    # ✅ المسار الرئيسي للـ router (بدون api/)
    path('', include(router.urls)),
    
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
  urlpatterns = [
    # ... مسارات أخرى ...
    
    # 🔔 مسارات الإشعارات
    path('notifications/unread-count/', views.NotificationViewSet.as_view({'get': 'unread_count'}), name='notification-unread-count'),
    path('notifications/mark-all-read/', views.NotificationViewSet.as_view({'post': 'mark_all_read'}), name='notification-mark-all-read'),
    path('notifications/stats/', views.NotificationViewSet.as_view({'get': 'stats'}), name='notification-stats'),
    path('notifications/recent/', views.NotificationViewSet.as_view({'get': 'recent'}), name='notification-recent'),
    path('notifications/archive/', views.NotificationViewSet.as_view({'get': 'archive', 'post': 'restore_from_archive'}), name='notification-archive'),
    path('notifications/delete-all-read/', views.NotificationViewSet.as_view({'delete': 'delete_all_read'}), name='notification-delete-all-read'),
    path('notifications/generate-auto/', views.NotificationViewSet.as_view({'post': 'generate_auto'}), name='notification-generate-auto'),  # ✅ هذا السطر يجب أن يكون هنا
    
    # ... مسارات أخرى ...
]
    # 📊 التقارير
    path('reports/all-data/', views.get_all_reports_data, name='reports-all-data'),
    
    # ✅ مسار الاختبار
    path('test-simple/', lambda request: JsonResponse({'status': 'ok', 'message': 'Test endpoint works!'})),
    
    # ✅ ماسح الباركود
    path('scan-barcode/', scan_barcode, name='scan-barcode'),
    path('watch/health-data/', views.watch_health_data, name='watch_health_data'),
    path('watch/history/', views.watch_history, name='watch_history'),
    path('watch/adb-data/', views.adb_watch_data, name='adb_watch_data'),
    
    # 🩺 الأدوية (بدون api/)
    path('medications/search/', views.search_medication, name='search-medication'),
    path('medications/<int:medication_id>/', views.get_medication_details, name='medication-details'),
    path('medications/user/', views.get_user_medications, name='user-medications'),
    path('medications/user/add/', views.add_user_medication, name='add-user-medication'),
    path('medications/user/<int:user_med_id>/delete/', views.delete_user_medication, name='delete-user-medication'),
    path('auth/google/', google_auth, name='google_auth'),
]