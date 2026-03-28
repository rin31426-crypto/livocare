from rest_framework import viewsets
from django.db.models import Sum, Avg, Count, Q  # يمكنك إضافة Q أيضاً إذا احتجته مستقبلاً
from .services.nutrition_service import NutritionService
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework import generics, permissions
from django.db.models import Sum, Avg
from rest_framework.response import Response
from datetime import date, timedelta
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, viewsets
from .services.cross_insights_service import HealthInsightsEngine
from django.utils import timezone
from .models import (
    PhysicalActivity, Sleep, MoodEntry, HealthStatus, Meal, 
    FoodItem, HabitDefinition, HabitLog, HealthGoal, 
    ChronicCondition, MedicalRecord, Recommendation, ChatLog, 
    Notification, EnvironmentData, CustomUser,
)
from .serializers import (
    PhysicalActivitySerializer, SleepSerializer, MoodEntrySerializer, 
    HealthStatusSerializer, MealSerializer, FoodItemSerializer, 
    HabitDefinitionSerializer, HabitLogSerializer, HealthGoalSerializer, 
    ChronicConditionSerializer, MedicalRecordSerializer, RecommendationSerializer, 
    ChatLogSerializer, NotificationSerializer, EnvironmentDataSerializer, UserRegistrationSerializer, UserProfileSerializer
)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    فقط المالك (user) يمكنه التعديل أو الحذف، ويتم دعم العلاقات الوسيطة (meal, habit).
    """
    def has_object_permission(self, request, view, obj):
        # السماح بالقراءة (SAFE_METHODS) للجميع (المصادق عليهم)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 1. حالة الارتباط المباشر (مثل PhysicalActivity, Sleep)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # 2. حالة الارتباط عبر الوجبة (FoodItem)
        elif hasattr(obj, 'meal') and hasattr(obj.meal, 'user'):
            return obj.meal.user == request.user
            
        # 3. حالة الارتباط عبر تعريف العادة (HabitLog)
        elif hasattr(obj, 'habit') and hasattr(obj.habit, 'user'):
            return obj.habit.user == request.user

        # إذا لم يتم العثور على علاقة واضحة للمالك، نرفض الوصول
        return False

# ---------------- ViewSets التي تستخدم user_id مباشرة ----------------

class BaseUserViewSet(viewsets.ModelViewSet):
    """ ViewSet أساسي لتبسيط الـ ViewSets التي ترتبط مباشرة بالمستخدم """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        # تصفية آمنة: عرض سجلات المستخدم الحالي فقط
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user) 
        return self.queryset.model.objects.none()
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# 1. النشاط البدني
class PhysicalActivityViewSet(BaseUserViewSet):
    queryset = PhysicalActivity.objects.all()
    serializer_class = PhysicalActivitySerializer

# 2. سجل النوم
class SleepViewSet(BaseUserViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer
    
# 3. سجل الحالة المزاجية
class MoodEntryViewSet(BaseUserViewSet):
    queryset = MoodEntry.objects.all()
    serializer_class = MoodEntrySerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            today_entry = MoodEntry.objects.filter(
                user=request.user,
                entry_time__gte=today_start
            ).order_by('-entry_time').first()

            if today_entry:
                serializer = self.get_serializer(today_entry)
                return Response(serializer.data)
            else:
                return Response({"message": "No mood entry found for today."}, status=204)
                
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=500)
    
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

# 4. القياسات الحيوية
class HealthStatusViewSet(BaseUserViewSet):
    queryset = HealthStatus.objects.all()
    serializer_class = HealthStatusSerializer

# 5. الوجبات
# 5. الوجبات
class MealViewSet(BaseUserViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    
    def perform_create(self, serializer):
        """إنشاء وجبة جديدة مع المكونات"""
        # الحصول على المكونات من البيانات المرسلة
        ingredients = self.request.data.get('ingredients', [])
        
        # حساب الإجماليات من المكونات
        total_calories = sum(i.get('calories', 0) for i in ingredients)
        total_protein = sum(i.get('protein', 0) for i in ingredients)
        total_carbs = sum(i.get('carbs', 0) for i in ingredients)
        total_fat = sum(i.get('fat', 0) for i in ingredients)
        
        # حفظ الوجبة مع المكونات والإجماليات
        serializer.save(
            user=self.request.user,
            ingredients=ingredients,
            total_calories=total_calories,
            total_protein=total_protein,
            total_carbs=total_carbs,
            total_fat=total_fat
        )
    
    def perform_update(self, serializer):
        """تحديث وجبة مع المكونات"""
        ingredients = self.request.data.get('ingredients', [])
        
        # إعادة حساب الإجماليات
        total_calories = sum(i.get('calories', 0) for i in ingredients)
        total_protein = sum(i.get('protein', 0) for i in ingredients)
        total_carbs = sum(i.get('carbs', 0) for i in ingredients)
        total_fat = sum(i.get('fat', 0) for i in ingredients)
        
        serializer.save(
            ingredients=ingredients,
            total_calories=total_calories,
            total_protein=total_protein,
            total_carbs=total_carbs,
            total_fat=total_fat
        )

# 6. تعريف العادة
class HabitDefinitionViewSet(BaseUserViewSet):
    queryset = HabitDefinition.objects.all()
    serializer_class = HabitDefinitionSerializer

# 7. الهدف الصحي
class HealthGoalViewSet(BaseUserViewSet):
    queryset = HealthGoal.objects.all()
    serializer_class = HealthGoalSerializer

# 8. الأمراض المزمنة
class ChronicConditionViewSet(BaseUserViewSet):
    queryset = ChronicCondition.objects.all()
    serializer_class = ChronicConditionSerializer

# 9. السجل الطبي
class MedicalRecordViewSet(BaseUserViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer

# 10. التوصيات
class RecommendationViewSet(BaseUserViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    http_method_names = ['get', 'head', 'options', 'put', 'patch', 'delete'] 
    
# 11. الإشعارات
class NotificationViewSet(BaseUserViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'head', 'options', 'put', 'patch', 'delete'] 
    
# 12. البيانات البيئية
class EnvironmentDataViewSet(BaseUserViewSet):
    queryset = EnvironmentData.objects.all()
    serializer_class = EnvironmentDataSerializer

# ---------------- ViewSets المتبقية (لا ترتبط مباشرة بالمستخدم) ----------------

# 13. المكون الغذائي (يرتبط بالوجبة وليس المستخدم مباشرة)
class FoodItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return FoodItem.objects.filter(meal__user=self.request.user).order_by('-meal__meal_time')
    
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    
# 14. سجل العادات (يرتبط بتعريف العادة وليس المستخدم مباشرة)
class HabitLogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return HabitLog.objects.filter(habit__user=self.request.user).order_by('-log_date')
    
    queryset = HabitLog.objects.all()
    serializer_class = HabitLogSerializer

class RegisterUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)     

# ✅ HealthSummaryView
class HealthSummaryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        today = date.today()
        
        activity_summary = PhysicalActivity.objects.filter(
            user=user,
            start_time__date=today
        ).aggregate(
            total_calories_burned=Sum('calories_burned'),
            total_duration_minutes=Sum('duration_minutes')
        )
        
        sleep_summary = Sleep.objects.filter(
            user=user,
            sleep_end__date=today
        ).aggregate(
            average_sleep_quality=Avg('quality_rating')
        )
        
        meal_summary = Meal.objects.filter(
            user=user,
            meal_time__date=today
        ).aggregate(
            total_calories_consumed=Sum('total_calories')
        )

        last_mood_entry = MoodEntry.objects.filter(
            user=user,
            entry_time__date=today
        ).order_by('-entry_time').first()
        
        current_mood = last_mood_entry.mood if last_mood_entry else "N/A"
        mood_count = MoodEntry.objects.filter(user=user, entry_time__date=today).count()
        
        last_health_status = HealthStatus.objects.filter(
            user=user
        ).order_by('-recorded_at').first()
        
        biometrics_data = {
            "last_weight_kg": last_health_status.weight_kg if last_health_status and last_health_status.weight_kg is not None else "N/A",
            "last_systolic_pressure": last_health_status.systolic_pressure if last_health_status and last_health_status.systolic_pressure is not None else "N/A",
            "last_diastolic_pressure": last_health_status.diastolic_pressure if last_health_status and last_health_status.diastolic_pressure is not None else "N/A",
            "last_glucose_mgdl": float(last_health_status.blood_glucose) if last_health_status and last_health_status.blood_glucose else "N/A",
            "last_blood_pressure": f"{last_health_status.systolic_pressure}/{last_health_status.diastolic_pressure}" 
                if last_health_status and last_health_status.systolic_pressure is not None and last_health_status.diastolic_pressure is not None else "N/A"
        }

        response_data = {
            "date": today.isoformat(),
            "activities": {
                "total_calories_burned": activity_summary.get('total_calories_burned') or 0,
                "total_duration_minutes": activity_summary.get('total_duration_minutes') or 0
            },
            "sleep": {
                "average_sleep_quality": round(sleep_summary.get('average_sleep_quality') or 0, 1)
            },
            "nutrition": {
                "total_calories_consumed": meal_summary.get('total_calories_consumed') or 0
            },
            "mood": {
                "last_recorded_mood": current_mood,
                "mood_entries_today": mood_count
            },
            "biometrics": biometrics_data,
            "status": "Summary data retrieved successfully."
        }
        
        return Response(response_data)

class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        return self.request.user
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        user = request.user
        
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
            
        elif request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)

# ==============================================================================
# 🆕 APIs الخارجية
# ==============================================================================

from rest_framework.decorators import api_view
from .services.weather_service import WeatherService
from .services.nutrition_service import NutritionService
from .services.exercise_service import AdvancedHealthAnalytics


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weather(request):
    try:
        city = request.query_params.get('city', 'Cairo')
        service = WeatherService()
        weather_data = service.get_weather(city)
        
        if weather_data and 'error' not in weather_data:
            return Response({
                'success': True,
                'data': weather_data
            })
        else:
            return Response({
                'success': False,
                'error': weather_data.get('error', 'تعذر جلب بيانات الطقس')
            }, status=500)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_food(request):
    try:
        query = request.query_params.get('query', '')
        if not query:
            return Response({
                'success': False,
                'error': 'الرجاء إدخال اسم الطعام'
            }, status=400)
        
        print(f"🔍 Food search request: {query}")
        
        service = NutritionService()
        results = service.search_food(query)
        
        return Response({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        print(f"❌ Error in search_food: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# أضف هذا في أعلى الملف مع الاستيرادات الأخرى
from .services.exercise_service import AdvancedHealthAnalytics  # ✅ استيراد ExerciseService

# ✅ التصحيح: استخدم AdvancedHealthAnalytics بدلاً من ExerciseService
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggest_exercises(request):
    try:
        # 🔥 تحديد اللغة من الطلب
        lang_param = request.query_params.get('lang')
        accept_lang = request.headers.get('Accept-Language', 'ar')
        
        if lang_param and lang_param in ['ar', 'en']:
            language = lang_param
        elif accept_lang.startswith('en'):
            language = 'en'
        else:
            language = 'ar'
        
        print(f"🏋️ Exercise suggestions requested with language: {language}")
        
        muscle = request.query_params.get('muscle')
        difficulty = request.query_params.get('difficulty')
        
        # ✅ تمرير اللغة إلى الخدمة
        service = AdvancedHealthAnalytics(request.user, language=language)
        exercises = service.suggest_exercises(muscle, difficulty)
        
        return Response({
            'success': True,
            'data': exercises
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_sentiment(request):
    try:
        text = request.data.get('text', '')
        if not text:
            return Response({
                'success': False,
                'error': 'الرجاء إدخال نص للتحليل'
            }, status=400)
        
        # استخدام SentimentAnalyzer الجديد مع Groq API
        from .services.sentiment_service import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(text)
        
        return Response({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"❌ Sentiment analysis error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_smart_recommendations(request):
    try:
        user = request.user
        
        latest_health = HealthStatus.objects.filter(user=user).first()
        latest_mood = MoodEntry.objects.filter(user=user).first()
        recent_activities = PhysicalActivity.objects.filter(
            user=user,
            start_time__date=date.today()
        ).count()
        
        weather_service = WeatherService()
        weather = weather_service.get_weather()
        
        recommendations = []
        
        if latest_health and latest_health.weight_kg:
            if latest_health.weight_kg > 90:
                recommendations.append({
                    'icon': '⚖️',
                    'message': 'وزنك أعلى من المعدل. جرب المشي 30 دقيقة يومياً'
                })
        
        if latest_mood and latest_mood.mood in ['Stressed', 'Anxious', 'Sad']:
            recommendations.append({
                'icon': '🧘',
                'message': 'مزاجك متعب اليوم. جرب تمارين التنفس العميق'
            })
        
        if recent_activities == 0:
            recommendations.append({
                'icon': '🚶',
                'message': 'لم تمارس أي نشاط اليوم. المشي 10 دقائق مفيد لصحتك'
            })
        
        if weather and not weather.get('error'):
            temp = weather.get('temperature', 25)
            if temp > 35:
                recommendations.append({
                    'icon': '🌡️',
                    'message': weather.get('recommendation', '')
                })
        
        return Response({
            'success': True,
            'data': recommendations
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ==============================================================================
# 🤖 الدردشة الذكية - Llama Service
# ==============================================================================

from .services.ai_chat_service import LlamaService

class ChatLogViewSet(BaseUserViewSet):
    queryset = ChatLog.objects.all()
    serializer_class = ChatLogSerializer
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """إرسال رسالة والحصول على رد ذكي"""
        message = request.data.get('message', '')
        
        if not message:
            return Response({'error': 'الرسالة مطلوبة'}, status=400)
        
        # حفظ رسالة المستخدم
        user_message = ChatLog.objects.create(
            user=request.user,
            sender='User',
            message_text=message,
            sentiment_score=0.0
        )
        
        # جلب آخر 20 رسالة للسياق (الأقدم أولاً)
        recent_messages = ChatLog.objects.filter(
            user=request.user
        ).order_by('timestamp')[:20]  # الأقدم أولاً للسياق
        
        chat_history = [
            {'sender': msg.sender, 'message': msg.message_text} 
            for msg in recent_messages
        ]
        
        # استخدام Llama Service
        try:
            print(f"📨 Message from {request.user.username}: {message[:50]}...")
            
            llama_service = LlamaService()
            bot_response = llama_service.get_chat_response(
                message, 
                request.user, 
                chat_history
            )
            
            print(f"✅ Response generated successfully")
            
        except Exception as e:
            print(f"❌ Critical error: {e}")
            bot_response = f"عذراً {request.user.username}، حدث خطأ غير متوقع."
        
        # حفظ رد المساعد
        bot_message = ChatLog.objects.create(
            user=request.user,
            sender='Bot',
            message_text=bot_response,
            sentiment_score=0.0
        )
        
        # ✅ جلب آخر 50 رسالة مرتبة بشكل صحيح (الأحدث أولاً للعرض)
        all_messages = ChatLog.objects.filter(
            user=request.user
        ).order_by('-timestamp')[:50]  # الأحدث أولاً للعرض
        
        # ✅ عكس الترتيب قبل الإرسال ليكون الأحدث في الأسفل
        messages_for_display = list(reversed(all_messages))
        
        serializer = self.get_serializer(messages_for_display, many=True)
        return Response(serializer.data, status=201)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """API منفصل لجلب تاريخ المحادثات بالترتيب الصحيح"""
        messages = ChatLog.objects.filter(
            user=request.user
        ).order_by('timestamp')  # الأقدم أولاً
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
# ==============================================================================
# 🧠 تحليلات ذكية متكاملة - مع دعم الترجمة
# ==============================================================================

def get_english_translation(key):
    """إرجاع الترجمة الإنجليزية للمفاتيح"""
    translations = {
        'analytics.habit.recommendations.sleep.title': 'Get Enough Sleep',
        'analytics.habit.recommendations.sleep.description': 'Goal: Improve mood and focus',
        'analytics.habit.recommendations.sleep.target': '7-8 hours',
        'analytics.habit.recommendations.habits.title': 'Stick to Daily Habits',
        'analytics.habit.recommendations.habits.description': 'Goal: Build consistency and discipline',
        'analytics.habit.recommendations.habits.target': 'Daily',
        'analytics.habit.recommendations.nutrition.title': 'Balanced Nutrition',
        'analytics.habit.recommendations.nutrition.description': 'Goal: Improve overall health',
        'analytics.habit.recommendations.nutrition.target': '5 servings',
        'analytics.habit.recommendations.water.title': 'Drink More Water',
        'analytics.habit.recommendations.water.description': 'Goal: Hydrate your body and boost energy',
        'analytics.habit.recommendations.water.target': '8 glasses',
        'analytics.habit.recommendations.exercise.title': 'Physical Activity',
        'analytics.habit.recommendations.exercise.description': 'Goal: Increase fitness and energy',
        'analytics.habit.recommendations.exercise.target': '30 minutes',
    }
    return translations.get(key, key)
# في views.py - استبدل دالة smart_insights بهذا
from .services.habit_analytics_service import HabitAnalyticsService

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_insights(request):
    """تحليلات ذكية متكاملة للعادات والعلاقات بين البيانات"""
    user = request.user
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # ✅ الحصول على اللغة من الطلب
    lang = request.GET.get('lang', 'ar')
    is_arabic = lang.startswith('ar')
    
    try:
        # 1. بيانات العادات
        habits = HabitDefinition.objects.filter(user=user)
        habit_logs = HabitLog.objects.filter(habit__user=user, log_date__gte=week_ago.date())
        
        total_habits = habits.count()
        completed_today = habit_logs.filter(log_date=today.date(), is_completed=True).count()
        completion_rate = 0
        if total_habits > 0:
            completion_rate = round((completed_today / total_habits) * 100)
        
        # 2. بيانات النوم
        sleep_data = Sleep.objects.filter(user=user, sleep_start__gte=week_ago)
        avg_sleep = sleep_data.aggregate(Avg('duration_hours'))['duration_hours__avg'] or 0
        avg_sleep = float(avg_sleep)
        
        # 3. بيانات المزاج
        mood_data = MoodEntry.objects.filter(user=user, entry_time__gte=week_ago)
        mood_counts = mood_data.values('mood').annotate(count=Count('mood'))
        dominant_mood = mood_counts.order_by('-count').first()
        
        # 4. بيانات النشاط
        activity_data = PhysicalActivity.objects.filter(user=user, start_time__gte=week_ago)
        activity_count = activity_data.count()
        
        # 5. بيانات التغذية
        meal_data = Meal.objects.filter(user=user, meal_time__gte=week_ago)
        avg_calories = meal_data.aggregate(Avg('total_calories'))['total_calories__avg'] or 0
        avg_calories = float(avg_calories)
        
        # 6. بيانات الوزن
        health_data = HealthStatus.objects.filter(user=user, recorded_at__gte=month_ago).order_by('recorded_at')
        
        # 7. متوسط العادات اليومية
        avg_habits = round(habit_logs.filter(is_completed=True).count() / 7, 1) if habit_logs.exists() else 0
        
        # 8. العلاقات
        correlations = []
        
        # العلاقة بين النوم والمزاج
        if sleep_data.exists() and mood_data.exists():
            bad_mood_days = mood_data.filter(mood__in=['Stressed', 'Anxious', 'Sad']).count()
            if avg_sleep < 6 and bad_mood_days > 2:
                correlations.append({
                    'icon': '😊',
                    'title': 'النوم والمزاج' if is_arabic else 'Sleep & Mood',
                    'description': f'عندما تنام أقل من 6 ساعات ({avg_sleep:.1f})، تزداد أيام المزاج السيئ' if is_arabic else f'When you sleep less than 6 hours ({avg_sleep:.1f}), bad mood days increase',
                    'strength': 0.7,
                    'sample_size': bad_mood_days
                })
        
        # العلاقة بين النشاط والوزن
        if activity_count > 0 and health_data.exists():
            correlations.append({
                'icon': '❤️',
                'title': 'النشاط البدني والوزن' if is_arabic else 'Physical Activity & Weight',
                'description': f'ممارسة الرياضة {activity_count} مرات أسبوعياً تساعد في الحفاظ على الوزن' if is_arabic else f'Exercising {activity_count} times weekly helps maintain weight',
                'strength': 0.75,
                'sample_size': activity_count
            })
        
        # العلاقة بين العادات والنوم
        if habit_logs.exists() and sleep_data.exists():
            high_habit_days = habit_logs.filter(is_completed=True).values('log_date').annotate(count=Count('id')).filter(count__gte=2)
            if high_habit_days.exists():
                correlations.append({
                    'icon': '💊',
                    'title': 'العادات والنوم' if is_arabic else 'Habits & Sleep',
                    'description': 'في الأيام التي تنجز فيها عاداتك، تنام بشكل أفضل' if is_arabic else 'On days you complete habits, you sleep better',
                    'strength': 0.65,
                    'sample_size': high_habit_days.count()
                })
        
        # ================== 9. التوصيات ==================
        recommendations = []
        
        if avg_sleep < 7:
            rec = {
                'icon': '🌙',
                'tips': [
                    'حدد موعداً ثابتاً للنوم' if is_arabic else 'Set a fixed bedtime',
                    'ابتعد عن الشاشات قبل النوم' if is_arabic else 'Avoid screens before sleep',
                    'تجنب الكافيين بعد العصر' if is_arabic else 'Avoid caffeine after 4 PM'
                ],
                'based_on': '7 أيام' if is_arabic else '7 days',
                'improvement_chance': 80
            }
            if is_arabic:
                rec['title'] = 'نم أكثر لتحسين صحتك'
                rec['description'] = 'الهدف: تحسين صحتك'
                rec['prediction'] = 'تحسن في المزاج والطاقة'
            else:
                rec['title'] = 'Get Enough Sleep'
                rec['description'] = 'Goal: Improve mood and focus'
                rec['prediction'] = 'Better mood and energy'
            recommendations.append(rec)
        
        if completion_rate < 50:
            rec = {
                'icon': '💊',
                'tips': [
                    'ابدأ بعادة صغيرة وسهلة' if is_arabic else 'Start with a small, easy habit',
                    'سجل عاداتك فور إنجازها' if is_arabic else 'Log habits immediately after completing',
                    'كافئ نفسك عند الإنجاز' if is_arabic else 'Reward yourself for achievements'
                ],
                'based_on': 'اليوم' if is_arabic else 'Today',
                'improvement_chance': 90
            }
            if is_arabic:
                rec['title'] = 'التزم بعاداتك اليومية'
                rec['description'] = 'الهدف: تحسين صحتك'
                rec['prediction'] = 'زيادة الإنتاجية والرضا'
            else:
                rec['title'] = 'Stick to Daily Habits'
                rec['description'] = 'Goal: Build consistency and discipline'
                rec['prediction'] = 'Increased productivity and satisfaction'
            recommendations.append(rec)
        
        if avg_calories < 1500:
            rec = {
                'icon': '🥗',
                'tips': [
                    'أضف وجبات خفيفة صحية' if is_arabic else 'Add healthy snacks',
                    'تناول البروتين في كل وجبة' if is_arabic else 'Include protein in every meal',
                    'اشرب الماء بانتظام' if is_arabic else 'Drink water regularly'
                ],
                'based_on': 'آخر أسبوع' if is_arabic else 'Last week',
                'improvement_chance': 85
            }
            if is_arabic:
                rec['title'] = 'نظام غذائي متوازن'
                rec['description'] = 'الهدف: تحسين صحتك'
                rec['prediction'] = 'طاقة أفضل وتركيز أعلى'
            else:
                rec['title'] = 'Balanced Nutrition'
                rec['description'] = 'Goal: Improve overall health'
                rec['prediction'] = 'Better energy and focus'
            recommendations.append(rec)
        
        # ================== 10. التنبؤات ==================
        last_weight = health_data.last().weight_kg if health_data.exists() else 70
        last_weight = float(last_weight) if last_weight else 70
        
        predictions = [
            {
                'icon': '⚖️',
                'label': 'الوزن المتوقع' if is_arabic else 'Expected Weight',
                'value': f"{last_weight - 0.5:.1f} كجم" if is_arabic else f"{last_weight - 0.5:.1f} kg",
                'trend': '⬇️ انخفاض طفيف' if is_arabic else '⬇️ Slight decrease',
                'note': 'مع استمرار النشاط البدني' if is_arabic else 'With continued physical activity'
            },
            {
                'icon': '🌙',
                'label': 'النوم المتوقع' if is_arabic else 'Expected Sleep',
                'value': f"{avg_sleep + 0.5:.1f} ساعات" if is_arabic else f"{avg_sleep + 0.5:.1f} hours",
                'trend': '⬆️ زيادة' if is_arabic else '⬆️ Increase',
                'note': 'إذا طبقت نصائح النوم' if is_arabic else 'If you apply sleep tips'
            },
            {
                'icon': '😊',
                'label': 'المزاج المتوقع' if is_arabic else 'Expected Mood',
                'value': dominant_mood['mood'] if dominant_mood else ('جيد' if is_arabic else 'Good'),
                'trend': '⬆️ تحسن' if is_arabic else '⬆️ Improvement',
                'note': 'مع تحسن النوم' if is_arabic else 'With improved sleep'
            }
        ]
        
        return Response({
            'success': True,
            'data': {
                'summary': {
                    'total_habits': total_habits,
                    'completed_today': completed_today,
                    'completion_rate': completion_rate,
                    'avg_sleep': round(avg_sleep, 1),
                    'dominant_mood': dominant_mood['mood'] if dominant_mood else ('غير متوفر' if is_arabic else 'Not available'),
                    'avg_habits': avg_habits,
                    'avg_calories': round(avg_calories)
                },
                'correlations': correlations,
                'recommendations': recommendations,
                'predictions': predictions
            }
        })
        
    except Exception as e:
        print(f"❌ Error in smart_insights: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
# ==============================================================================
# 🥗 تحليلات التغذية
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_insights(request):
    """تحليلات التغذية المتقدمة - تحسب من الوجبات مباشرة"""
    user = request.user
    meals = Meal.objects.filter(user=user)
    
    if not meals.exists():
        return Response({
            'total_meals': 0,
            'avg_calories': 0,
            'avg_protein': 0,
            'avg_carbs': 0,
            'avg_fat': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'meal_distribution': {},
            'trend': 'insufficient_data',
            'recommendations': [],
            'date': timezone.now().isoformat()
        })
    
    # حساب الإجماليات من الوجبات مباشرة
    total_meals = meals.count()
    
    # استخدام aggregate للحصول على المجاميع
    totals = meals.aggregate(
        total_calories=Sum('total_calories'),
        total_protein=Sum('total_protein'),
        total_carbs=Sum('total_carbs'),
        total_fat=Sum('total_fat')
    )
    
    total_calories = totals['total_calories'] or 0
    total_protein = totals['total_protein'] or 0
    total_carbs = totals['total_carbs'] or 0
    total_fat = totals['total_fat'] or 0
    
    # حساب المتوسطات
    avg_calories = total_calories / total_meals if total_meals > 0 else 0
    avg_protein = total_protein / total_meals if total_meals > 0 else 0
    avg_carbs = total_carbs / total_meals if total_meals > 0 else 0
    avg_fat = total_fat / total_meals if total_meals > 0 else 0
    
    # توزيع الوجبات
    meal_distribution = meals.values('meal_type').annotate(count=Count('id'))
    distribution_dict = {item['meal_type']: item['count'] for item in meal_distribution}
    
    # طباعة للتشخيص
    print(f"✅ Nutrition insights - User: {user.username}")
    print(f"   Total meals: {total_meals}")
    print(f"   Total calories: {total_calories}")
    print(f"   Avg calories: {avg_calories}")
    print(f"   Distribution: {distribution_dict}")
    
    return Response({
        'total_meals': total_meals,
        'avg_calories': round(avg_calories, 1),
        'avg_protein': round(float(avg_protein), 1),
        'avg_carbs': round(float(avg_carbs), 1),
        'avg_fat': round(float(avg_fat), 1),
        'total_protein': round(float(total_protein), 1),
        'total_carbs': round(float(total_carbs), 1),
        'total_fat': round(float(total_fat), 1),
        'meal_distribution': distribution_dict,
        'trend': 'stable',
        'recommendations': [],
        'date': timezone.now().isoformat()
    })
# ==============================================================================
# 🎯 الرؤى المتقاطعة المتقدمة (Advanced Cross Insights)
# ==============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advanced_cross_insights(request):
    """
    تحليلات متقاطعة متقدمة (الطاقة، ضغط النبض، مخاطر التمرين)
    """
    try:
        # 🔥 تحديد اللغة من الطلب
        lang_param = request.query_params.get('lang')
        accept_lang = request.headers.get('Accept-Language', 'ar')
        
        if lang_param and lang_param in ['ar', 'en']:
            language = lang_param
        elif accept_lang.startswith('en'):
            language = 'en'
        else:
            language = 'ar'
        
        print(f"🌐 Advanced insights requested with language: {language}")
        
        # ✅ تصحيح اسم الكلاس هنا
        engine = HealthInsightsEngine(request.user, language=language)
        
        # استخدام الدوال الجديدة
        data = {
            'energy_consumption': engine.analyze_energy_consumption(),
            'pulse_pressure': engine.analyze_pulse_pressure(),
            'pre_exercise': engine.analyze_pre_exercise_risk(),
            'vital_signs': engine.analyze_vital_signs(),
            'holistic': engine.generate_holistic_recommendations(),
            'predictive': engine.generate_predictive_alerts()
        }
        
        return Response({
            'success': True,
            'data': data,
            'message': 'تم تحليل العلاقات الصحية المتقدمة بنجاح'
        })
    except Exception as e:
        print(f"❌ Error in advanced_cross_insights: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
    
# يمكنك الاحتفاظ بالقديم للتوافقية إذا أردت
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cross_insights(request):
    """
    تحليلات متقاطعة أساسية (للتوافق مع الإصدارات السابقة)
    """
    try:
        from .services.cross_insights_service import CrossInsightsService
        service = CrossInsightsService(request.user)
        insights = service.get_all_correlations()
        
        return Response({
            'success': True,
            'data': insights,
            'message': 'تم تحليل العلاقات الصحية بنجاح'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# 11. الإشعارات - نسخة كاملة ومحسنة
class NotificationViewSet(BaseUserViewSet):
    """
    ViewSet متكامل لإدارة الإشعارات
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'post', 'head', 'options', 'put', 'patch', 'delete']
    
    def get_queryset(self):
        """تصفية الإشعارات حسب المستخدم"""
        return Notification.objects.filter(
            user=self.request.user,
            is_archived=False
        ).order_by('-sent_at')
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """الحصول على عدد الإشعارات غير المقروءة"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_archived=False
        ).count()
        return Response({'count': count})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """تحديد كل الإشعارات كمقروءة"""
        Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_archived=False
        ).update(is_read=True, read_at=timezone.now())
        
        # جلب العدد الجديد
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_archived=False
        ).count()
        
        return Response({
            'status': 'success',
            'message': 'تم تحديد جميع الإشعارات كمقروءة',
            'unread_count': count
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """تحديد إشعار معين كمقروء"""
        notification = self.get_object()
        notification.mark_as_read()  # استخدام الدالة من الموديل
        
        return Response({
            'status': 'success',
            'message': 'تم تحديد الإشعار كمقروء'
        })
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """تصفية الإشعارات حسب النوع"""
        notification_type = request.query_params.get('type')
        if not notification_type:
            return Response({
                'error': 'معامل type مطلوب'
            }, status=400)
        
        notifications = self.get_queryset().filter(type=notification_type)
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_priority(self, request):
        """تصفية الإشعارات حسب الأولوية"""
        priority = request.query_params.get('priority')
        if not priority:
            return Response({
                'error': 'معامل priority مطلوب'
            }, status=400)
        
        notifications = self.get_queryset().filter(priority=priority)
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """آخر 10 إشعارات"""
        limit = int(request.query_params.get('limit', 10))
        notifications = self.get_queryset()[:limit]
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """حذف كل الإشعارات المقروءة"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=True,
            is_archived=False
        ).update(is_archived=True)
        
        return Response({
            'status': 'success',
            'message': f'تم أرشفة {count} إشعار مقروء',
            'archived_count': count
        })
    
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        """حذف كل الإشعارات (نقل إلى الأرشيف)"""
        count = Notification.objects.filter(
            user=request.user,
            is_archived=False
        ).update(is_archived=True)
        
        return Response({
            'status': 'success',
            'message': f'تم أرشفة {count} إشعار',
            'archived_count': count
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """إحصائيات متقدمة للإشعارات"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # إحصائيات أساسية
        total = Notification.objects.filter(
            user=request.user,
            is_archived=False
        ).count()
        
        unread = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_archived=False
        ).count()
        
        read = total - unread
        
        # إحصائيات حسب النوع
        by_type = Notification.objects.filter(
            user=request.user,
            is_archived=False
        ).values('type').annotate(count=Count('id'))
        
        type_dict = {item['type']: item['count'] for item in by_type}
        
        # إحصائيات حسب الأولوية
        by_priority = Notification.objects.filter(
            user=request.user,
            is_archived=False
        ).values('priority').annotate(count=Count('id'))
        
        priority_dict = {item['priority']: item['count'] for item in by_priority}
        
        # آخر 7 أيام
        last_7_days = Notification.objects.filter(
            user=request.user,
            sent_at__date__gte=week_ago,
            is_archived=False
        ).count()
        
        # آخر 30 يوم
        last_30_days = Notification.objects.filter(
            user=request.user,
            sent_at__date__gte=month_ago,
            is_archived=False
        ).count()
        
        return Response({
            'total': total,
            'unread': unread,
            'read': read,
            'by_type': type_dict,
            'by_priority': priority_dict,
            'last_7_days': last_7_days,
            'last_30_days': last_30_days,
            'archive_url': '/api/notifications/archive/'
        })
    
    @action(detail=False, methods=['get'])
    def archive(self, request):
        """عرض الإشعارات المؤرشفة"""
        archived = Notification.objects.filter(
            user=request.user,
            is_archived=True
        ).order_by('-sent_at')
        
        # دعم التصفية حسب الصفحات
        page = self.paginate_queryset(archived)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(archived, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def restore_from_archive(self, request):
        """استعادة إشعارات من الأرشيف"""
        notification_ids = request.data.get('ids', [])
        
        if not notification_ids:
            return Response({
                'error': 'قائمة ids مطلوبة'
            }, status=400)
        
        count = Notification.objects.filter(
            user=request.user,
            id__in=notification_ids,
            is_archived=True
        ).update(is_archived=False)
        
        return Response({
            'status': 'success',
            'message': f'تم استعادة {count} إشعار',
            'restored_count': count
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """البحث في الإشعارات"""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({
                'error': 'الاستعلام يجب أن يكون حرفين على الأقل'
            }, status=400)
        
        notifications = self.get_queryset().filter(
            Q(title__icontains=query) | Q(message__icontains=query)
        )
        
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'query': query,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def create_test_notification(self, request):
        """
        إنشاء إشعار تجريبي (للتطوير والاختبار فقط)
        """
        if not request.user.is_staff:  # فقط للمشرفين
            return Response({
                'error': 'غير مصرح به'
            }, status=403)
        
        notification = Notification.objects.create(
            user=request.user,
            type='alert',
            priority='high',
            icon='⚠️',
            title='⚠️ إشعار تجريبي',
            message='هذا إشعار تجريبي للاختبار',
            suggestions=['اقتراح 1', 'اقتراح 2', 'اقتراح 3']
        )
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=201)
# ==============================================================================
# 📊 API خاص بالتقارير الشاملة
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_reports_data(request):
    """جلب جميع بيانات التقارير دفعة واحدة (النوم، المزاج، النشاط، العادات)"""
    user = request.user
    today = timezone.now().date()
    
    try:
        # جلب بيانات النوم لآخر 30 يوم
        sleep_data = Sleep.objects.filter(
            user=user,
            sleep_start__date__gte=today - timedelta(days=30)
        ).values(
            'id', 'sleep_start', 'sleep_end', 'duration_hours', 'quality_rating'
        ).order_by('-sleep_start')
        
        # جلب بيانات المزاج
        mood_data = MoodEntry.objects.filter(
            user=user,
            entry_time__date__gte=today - timedelta(days=30)
        ).values(
            'id', 'entry_time', 'mood', 'factors'
        ).order_by('-entry_time')
        
        # جلب بيانات النشاط البدني
        activity_data = PhysicalActivity.objects.filter(
            user=user,
            start_time__date__gte=today - timedelta(days=30)
        ).values(
            'id', 'start_time', 'activity_type', 'duration_minutes', 'calories_burned'
        ).order_by('-start_time')
        
        # جلب بيانات العادات مع اسم العادة
        habit_data = HabitLog.objects.filter(
            habit__user=user,
            log_date__gte=today - timedelta(days=30)
        ).select_related('habit').values(
            'id', 'log_date', 'habit__name', 'is_completed'
        ).order_by('-log_date')
        
        print(f"📊 Reports data for {user.username}:")
        print(f"   Sleep: {len(sleep_data)} records")
        print(f"   Mood: {len(mood_data)} records")
        print(f"   Activity: {len(activity_data)} records")
        print(f"   Habits: {len(habit_data)} records")
        
        return Response({
            'sleep': list(sleep_data),
            'mood': list(mood_data),
            'activity': list(activity_data),
            'habits': list(habit_data)
        })
        
    except Exception as e:
        print(f"❌ Error in get_all_reports_data: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'sleep': [],
            'mood': [],
            'activity': [],
            'habits': [],
            'error': str(e)
        }, status=500)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comprehensive_analytics(request):
    """
    الحصول على تحليلات شاملة باستخدام التعلم الآلي
    """
    try:
        # 🔥 تحديد اللغة من الطلب
        lang_param = request.query_params.get('lang')
        accept_lang = request.headers.get('Accept-Language', 'ar')
        
        if lang_param and lang_param in ['ar', 'en']:
            language = lang_param
        elif accept_lang.startswith('en'):
            language = 'en'
        else:
            language = 'ar'
        
        print(f"📊 Comprehensive analytics requested with language: {language}")
        
        # ✅ تمرير اللغة إلى الخدمة
        service = AdvancedHealthAnalytics(request.user, language=language)
        analytics = service.get_comprehensive_analytics()
        
        return Response({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        print(f"❌ Error in comprehensive analytics: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# إضافة في views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import HealthStatus
# أضف هذا الاستيراد في أعلى الملف (إذا لم يكن موجوداً)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import HealthStatus
import json
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def watch_health_data(request):
    """استقبال بيانات الساعة الذكية"""
    try:
        data = request.data
        logger.info(f"📱 Watch health data received: {data}")
        
        # استخراج البيانات (مرنة لاستقبال تنسيقات مختلفة)
        heart_rate = data.get('heart_rate') or data.get('heartRate')
        systolic = data.get('systolic_pressure') or data.get('systolic')
        diastolic = data.get('diastolic_pressure') or data.get('diastolic')
        recorded_at = data.get('recorded_at') or data.get('timestamp') or timezone.now()
        
        # تحويل التاريخ إذا كان نصاً
        if isinstance(recorded_at, str):
            try:
                recorded_at = timezone.datetime.fromisoformat(recorded_at.replace('Z', '+00:00'))
            except:
                recorded_at = timezone.now()
        
        # حفظ البيانات
        health_data = HealthStatus.objects.create(
            user=request.user,
            heart_rate=heart_rate,
            systolic_pressure=systolic,
            diastolic_pressure=diastolic,
            recorded_at=recorded_at
        )
        
        logger.info(f"✅ Health data saved: HR={heart_rate}, BP={systolic}/{diastolic}")
        
        # تنبيه للقراءات غير الطبيعية
        alerts = []
        if health_data.heart_rate:
            if health_data.heart_rate > 100:
                alerts.append(f"⚠️ ارتفاع ضربات القلب: {health_data.heart_rate} BPM")
            elif health_data.heart_rate < 60:
                alerts.append(f"⚠️ انخفاض ضربات القلب: {health_data.heart_rate} BPM")
        
        if health_data.systolic_pressure and health_data.diastolic_pressure:
            if health_data.systolic_pressure > 140 or health_data.diastolic_pressure > 90:
                alerts.append(f"⚠️ ارتفاع ضغط الدم: {health_data.systolic_pressure}/{health_data.diastolic_pressure}")
            elif health_data.systolic_pressure < 90 or health_data.diastolic_pressure < 60:
                alerts.append(f"⚠️ انخفاض ضغط الدم: {health_data.systolic_pressure}/{health_data.diastolic_pressure}")
        
        return Response({
            'success': True,
            'data': {
                'id': health_data.id,
                'heart_rate': health_data.heart_rate,
                'blood_pressure': f"{health_data.systolic_pressure}/{health_data.diastolic_pressure}" if health_data.systolic_pressure else None,
                'recorded_at': health_data.recorded_at.isoformat()
            },
            'alerts': alerts
        })
        
    except Exception as e:
        logger.error(f"❌ Error saving watch data: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def watch_history(request):
    """جلب تاريخ بيانات الساعة"""
    try:
        # جلب آخر 50 قراءة
        data = HealthStatus.objects.filter(
            user=request.user
        ).order_by('-recorded_at')[:50]
        
        # إضافة نوع البيانات للتمييز
        result = []
        for item in data:
            result.append({
                'id': item.id,
                'heart_rate': item.heart_rate,
                'systolic_pressure': item.systolic_pressure,
                'diastolic_pressure': item.diastolic_pressure,
                'recorded_at': item.recorded_at.isoformat(),
                'source': 'watch'  # تحديد أن البيانات من الساعة
            })
        
        return Response({
            'success': True,
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching watch history: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


# ✅ API إضافي لاستقبال البيانات من ADB Monitor
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def adb_watch_data(request):
    """
    استقبال بيانات الساعة من ADB Monitor
    التنسيق المتوقع:
    {
        "heart_rate": 82,
        "systolic": 118,
        "diastolic": 76,
        "timestamp": "2024-01-01T12:00:00"
    }
    """
    try:
        data = request.data
        logger.info(f"📡 ADB Watch data received: {data}")
        
        # استخراج البيانات
        heart_rate = data.get('heart_rate') or data.get('heartRate')
        systolic = data.get('systolic') or data.get('systolic_pressure')
        diastolic = data.get('diastolic') or data.get('diastolic_pressure')
        timestamp = data.get('timestamp') or data.get('recorded_at') or timezone.now()
        
        # التحقق من صحة البيانات
        if not heart_rate and not systolic:
            return Response({
                'success': False,
                'error': 'لا توجد بيانات صحية في الطلب'
            }, status=400)
        
        # حفظ البيانات
        health_data = HealthStatus.objects.create(
            user=request.user,
            heart_rate=heart_rate,
            systolic_pressure=systolic,
            diastolic_pressure=diastolic,
            recorded_at=timestamp
        )
        
        logger.info(f"✅ ADB data saved: ID={health_data.id}, HR={heart_rate}, BP={systolic}/{diastolic}")
        
        # إنشاء إشعار للتطبيق
        from .models import Notification
        if heart_rate and (heart_rate > 100 or heart_rate < 60):
            Notification.objects.create(
                user=request.user,
                type='health_alert',
                priority='high',
                icon='❤️',
                title='تنبيه صحي',
                message=f'ضربات القلب: {heart_rate} BPM',
                suggestions=['استرح قليلاً', 'خذ نفساً عميقاً', 'اشرب ماء']
            )
        
        return Response({
            'success': True,
            'message': 'تم استلام بيانات الساعة بنجاح',
            'data': {
                'id': health_data.id,
                'heart_rate': health_data.heart_rate,
                'blood_pressure': f"{health_data.systolic_pressure}/{health_data.diastolic_pressure}" if health_data.systolic_pressure else None,
                'recorded_at': health_data.recorded_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ ADB data error: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
# analytics/views.py - أضف في نهاية الملف
# ==============================================================================
# 📷 مسح الباركود - الاتصال بخدمة الكاميرا
# ==============================================================================

import requests
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import json

@csrf_exempt
@api_view(['POST'])
def scan_barcode(request):
    try:
        data = json.loads(request.body)
        camera_url = os.environ.get('CAMERA_SERVICE_URL', 'https://camera-service-fag3.onrender.com')
        
        response = requests.post(
            f"{camera_url}/scan-barcode",
            json={'image': data.get('image', '')},
            timeout=10
        )
        
        return JsonResponse(response.json(), status=response.status_code)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import json

@api_view(['GET'])
@permission_classes([AllowAny])
def test_websocket(request):
    """
    دالة اختبارية للتحقق من عمل WebSocket
    """
    return Response({
        'success': True,
        'message': 'WebSocket API is working',
        'websocket_url': 'ws://localhost:8000/ws/watch/',
        'status': 'ok'
    })