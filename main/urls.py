from django.urls import path, include
from rest_framework.routers import DefaultRouter
from main import views

# ✅ استيراد الدالة scan_barcode
from main.views import scan_barcode

router = DefaultRouter()
# الروابط التي تم تأكيدها
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

urlpatterns = [
    # ✅ المسار الرئيسي للـ router
    path('', include(router.urls)),
    
    # ✅ مسار /api/
    path('api/', include(router.urls)),
    
    # 🌤️ الطقس
    path('api/weather/', views.get_weather, name='weather'),
    
    # 🥗 التغذية والبحث عن الطعام
    path('api/food/search/', views.search_food, name='food-search'),
    
    # 💪 التمارين الرياضية
    path('api/exercises/suggest/', views.suggest_exercises, name='exercise-suggest'),
    
    # 😊 تحليل المشاعر
    path('api/sentiment/analyze/', views.analyze_sentiment, name='sentiment-analyze'),
    
    # 💡 التوصيات الذكية
    path('api/smart-recommendations/', views.get_smart_recommendations, name='smart-recommendations'),
    
    # 🧠 تحليلات ذكية متكاملة
    path('api/analytics/smart-insights/', views.smart_insights, name='smart-insights'),
    path('api/cross-insights/', views.cross_insights, name='cross-insights'),
    path('api/advanced-insights/', views.advanced_cross_insights, name='advancedHealthInsights'),
    
    # 🔔 مسارات الإشعارات
    path('api/notifications/unread-count/', 
         views.NotificationViewSet.as_view({'get': 'unread_count'}), 
         name='notification-unread-count'),
    
    path('api/notifications/mark-all-read/', 
         views.NotificationViewSet.as_view({'post': 'mark_all_read'}), 
         name='notification-mark-all-read'),
    
    path('api/notifications/stats/', 
         views.NotificationViewSet.as_view({'get': 'stats'}), 
         name='notification-stats'),
    
    path('api/notifications/recent/', 
         views.NotificationViewSet.as_view({'get': 'recent'}), 
         name='notification-recent'),
    
    path('api/notifications/archive/', 
         views.NotificationViewSet.as_view({'get': 'archive', 'post': 'restore_from_archive'}), 
         name='notification-archive'),
    
    path('api/notifications/delete-all-read/', 
         views.NotificationViewSet.as_view({'delete': 'delete_all_read'}), 
         name='notification-delete-all-read'),
    
    # 📊 التقارير
    path('api/reports/all-data/', views.get_all_reports_data, name='reports-all-data'),
    
    # ✅ ماسح الباركود - الآن يعمل بعد إضافة الاستيراد
    path('api/scan-barcode/', scan_barcode, name='scan-barcode'),
    path('api/watch/health-data/', views.watch_health_data, name='watch_health_data'),
    path('api/watch/history/', views.watch_history, name='watch_history'),
    path('api/watch/adb-data/', views.adb_watch_data, name='adb_watch_data'),
]

# ==============================================================================
# 📋 قائمة بجميع مسارات الإشعارات المتاحة (للتوثيق)
# ==============================================================================

"""
📋 قائمة مسارات الإشعارات الكاملة:

🔹 GET    /api/notifications/                  - قائمة جميع الإشعارات
🔹 GET    /api/notifications/{id}/             - عرض إشعار محدد
🔹 POST   /api/notifications/                   - إنشاء إشعار جديد
🔹 PUT    /api/notifications/{id}/             - تحديث إشعار
🔹 PATCH  /api/notifications/{id}/             - تحديث جزئي
🔹 DELETE /api/notifications/{id}/             - حذف إشعار

🔹 GET    /api/notifications/unread_count/     - عدد الإشعارات غير المقروءة
🔹 POST   /api/notifications/mark_all_read/    - تحديد الكل كمقروء
🔹 POST   /api/notifications/{id}/mark_read/   - تحديد إشعار محدد كمقروء
🔹 GET    /api/notifications/by_type/?type=    - تصفية حسب النوع
🔹 GET    /api/notifications/by_priority/?priority= - تصفية حسب الأولوية
🔹 GET    /api/notifications/recent/           - آخر 10 إشعارات
🔹 GET    /api/notifications/stats/            - إحصائيات متقدمة
🔹 GET    /api/notifications/archive/          - عرض الإشعارات المؤرشفة
🔹 POST   /api/notifications/archive/          - استعادة من الأرشيف
🔹 DELETE /api/notifications/delete-all-read/  - حذف كل المقروء
🔹 DELETE /api/notifications/delete-all/       - حذف الكل
🔹 GET    /api/notifications/search/?q=        - البحث في الإشعارات
🔹 POST   /api/notifications/create_test_notification/ - إنشاء إشعار تجريبي
"""