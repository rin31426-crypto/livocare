# main/views.py
# ==============================================================================
# 📦 الاستيرادات
# ==============================================================================

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import requests
import json
import logging
from rest_framework import permissions
from django.conf import settings
from django.views.decorators.http import require_http_methods
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
    ChatLogSerializer, NotificationSerializer, EnvironmentDataSerializer, 
    UserRegistrationSerializer, UserProfileSerializer
)
from .services.nutrition_service import NutritionService
from .services.weather_service import WeatherService
from .services.exercise_service import AdvancedHealthAnalytics
from .services.cross_insights_service import HealthInsightsEngine
from .services.habit_analytics_service import HabitAnalyticsService
from .services.ai_chat_service import LlamaService
from .services.sentiment_service import SentimentAnalyzer
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)
User = get_user_model()

# ==============================================================================
# 🔐 أذونات مخصصة
# ==============================================================================

class IsOwnerOrReadOnly(permissions.BasePermission):
    """فقط المالك يمكنه التعديل أو الحذف"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'meal') and hasattr(obj.meal, 'user'):
            return obj.meal.user == request.user
        elif hasattr(obj, 'habit') and hasattr(obj.habit, 'user'):
            return obj.habit.user == request.user
        
        return False


class BaseUserViewSet(viewsets.ModelViewSet):
    """ViewSet أساسي للموديلات المرتبطة بالمستخدم"""
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.queryset.model.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==============================================================================
# 📊 ViewSets الأساسية
# ==============================================================================

class PhysicalActivityViewSet(BaseUserViewSet):
    queryset = PhysicalActivity.objects.all()
    serializer_class = PhysicalActivitySerializer


class SleepViewSet(BaseUserViewSet):
    queryset = Sleep.objects.all()
    serializer_class = SleepSerializer


class MoodEntryViewSet(BaseUserViewSet):
    queryset = MoodEntry.objects.all()
    serializer_class = MoodEntrySerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_entry = MoodEntry.objects.filter(
            user=request.user, entry_time__gte=today_start
        ).order_by('-entry_time').first()
        
        if today_entry:
            serializer = self.get_serializer(today_entry)
            return Response(serializer.data)
        return Response({"message": "No mood entry found for today."}, status=204)


class HealthStatusViewSet(BaseUserViewSet):
    queryset = HealthStatus.objects.all()
    serializer_class = HealthStatusSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=request.user)
        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class MealViewSet(BaseUserViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    
    def perform_create(self, serializer):
        ingredients = self.request.data.get('ingredients', [])
        total_calories = sum(i.get('calories', 0) for i in ingredients)
        total_protein = sum(i.get('protein', 0) for i in ingredients)
        total_carbs = sum(i.get('carbs', 0) for i in ingredients)
        total_fat = sum(i.get('fat', 0) for i in ingredients)
        
        serializer.save(
            user=self.request.user,
            ingredients=ingredients,
            total_calories=total_calories,
            total_protein=total_protein,
            total_carbs=total_carbs,
            total_fat=total_fat
        )


class HabitDefinitionViewSet(BaseUserViewSet):
    queryset = HabitDefinition.objects.all()
    serializer_class = HabitDefinitionSerializer


class HealthGoalViewSet(BaseUserViewSet):
    queryset = HealthGoal.objects.all()
    serializer_class = HealthGoalSerializer


class ChronicConditionViewSet(BaseUserViewSet):
    queryset = ChronicCondition.objects.all()
    serializer_class = ChronicConditionSerializer


class MedicalRecordViewSet(BaseUserViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer


class RecommendationViewSet(BaseUserViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    http_method_names = ['get', 'head', 'options', 'put', 'patch', 'delete']


class EnvironmentDataViewSet(BaseUserViewSet):
    queryset = EnvironmentData.objects.all()
    serializer_class = EnvironmentDataSerializer


class FoodItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemSerializer
    
    def get_queryset(self):
        return FoodItem.objects.filter(meal__user=self.request.user).order_by('-meal__meal_time')


class HabitLogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = HabitLogSerializer
    
    def get_queryset(self):
        return HabitLog.objects.filter(habit__user=self.request.user).order_by('-log_date')
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        logs = HabitLog.objects.filter(habit__user=request.user, log_date=today).select_related('habit')
        all_habits = HabitDefinition.objects.filter(user=request.user, is_active=True)
        
        result = []
        log_habit_ids = logs.values_list('habit_id', flat=True)
        
        for log in logs:
            result.append({
                'id': log.id,
                'habit': {'id': log.habit.id, 'name': log.habit.name, 'description': log.habit.description},
                'is_completed': log.is_completed,
                'actual_value': log.actual_value,
                'notes': log.notes,
                'log_date': log.log_date,
            })
        
        for habit in all_habits:
            if habit.id not in log_habit_ids:
                result.append({
                    'id': None,
                    'habit': {'id': habit.id, 'name': habit.name, 'description': habit.description},
                    'is_completed': False,
                    'actual_value': None,
                    'notes': None,
                    'log_date': today,
                })
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def complete(self, request):
        from django.utils import timezone
        habit_id = request.data.get('habit_id')
        actual_value = request.data.get('actual_value')
        notes = request.data.get('notes', '')
        
        if not habit_id:
            return Response({'error': 'habit_id مطلوب'}, status=400)
        
        try:
            habit = HabitDefinition.objects.get(id=habit_id, user=request.user)
        except HabitDefinition.DoesNotExist:
            return Response({'error': 'العادة غير موجودة'}, status=404)
        
        today = timezone.now().date()
        log, created = HabitLog.objects.update_or_create(
            habit=habit, log_date=today,
            defaults={'is_completed': True, 'actual_value': actual_value, 'notes': notes}
        )
        
        serializer = self.get_serializer(log)
        return Response(serializer.data)


# ==============================================================================
# 👤 إدارة المستخدمين
# ==============================================================================

class RegisterUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)


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
# 📊 التقارير والملخصات
# ==============================================================================

class HealthSummaryView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = date.today()
        
        activity_summary = PhysicalActivity.objects.filter(
            user=user, start_time__date=today
        ).aggregate(total_calories_burned=Sum('calories_burned'), total_duration_minutes=Sum('duration_minutes'))
        
        sleep_summary = Sleep.objects.filter(
            user=user, sleep_end__date=today
        ).aggregate(average_sleep_quality=Avg('quality_rating'))
        
        meal_summary = Meal.objects.filter(
            user=user, meal_time__date=today
        ).aggregate(total_calories_consumed=Sum('total_calories'))
        
        last_mood_entry = MoodEntry.objects.filter(user=user, entry_time__date=today).order_by('-entry_time').first()
        current_mood = last_mood_entry.mood if last_mood_entry else "N/A"
        
        last_health_status = HealthStatus.objects.filter(user=user).order_by('-recorded_at').first()
        
        return Response({
            "date": today.isoformat(),
            "activities": {
                "total_calories_burned": activity_summary.get('total_calories_burned') or 0,
                "total_duration_minutes": activity_summary.get('total_duration_minutes') or 0
            },
            "sleep": {"average_sleep_quality": round(sleep_summary.get('average_sleep_quality') or 0, 1)},
            "nutrition": {"total_calories_consumed": meal_summary.get('total_calories_consumed') or 0},
            "mood": {"last_recorded_mood": current_mood},
            "biometrics": {
                "last_weight_kg": last_health_status.weight_kg if last_health_status else "N/A",
                "last_blood_pressure": f"{last_health_status.systolic_pressure}/{last_health_status.diastolic_pressure}" if last_health_status else "N/A"
            }
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_reports_data(request):
    """جلب جميع بيانات التقارير دفعة واحدة"""
    user = request.user
    today = timezone.now().date()
    
    sleep_data = Sleep.objects.filter(user=user, sleep_start__date__gte=today - timedelta(days=30)).values(
        'id', 'sleep_start', 'sleep_end', 'duration_hours', 'quality_rating'
    ).order_by('-sleep_start')
    
    mood_data = MoodEntry.objects.filter(user=user, entry_time__date__gte=today - timedelta(days=30)).values(
        'id', 'entry_time', 'mood', 'factors'
    ).order_by('-entry_time')
    
    activity_data = PhysicalActivity.objects.filter(user=user, start_time__date__gte=today - timedelta(days=30)).values(
        'id', 'start_time', 'activity_type', 'duration_minutes', 'calories_burned'
    ).order_by('-start_time')
    
    habit_data = HabitLog.objects.filter(habit__user=user, log_date__gte=today - timedelta(days=30)).select_related('habit').values(
        'id', 'log_date', 'habit__name', 'is_completed'
    ).order_by('-log_date')
    
    return Response({
        'sleep': list(sleep_data),
        'mood': list(mood_data),
        'activity': list(activity_data),
        'habits': list(habit_data)
    })


# ==============================================================================
# 🌤️ APIs الخارجية - الطقس، الطعام، التمارين
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weather(request):
    try:
        city = request.query_params.get('city', 'Cairo')
        service = WeatherService()
        weather_data = service.get_weather(city)
        
        if weather_data and 'error' not in weather_data:
            return Response({'success': True, 'data': weather_data})
        return Response({'success': False, 'error': weather_data.get('error', 'تعذر جلب بيانات الطقس')}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_food(request):
    """البحث عن الطعام باستخدام Open Food Facts API"""
    try:
        query = request.query_params.get('query', '')
        if not query:
            return Response({'success': False, 'error': 'الرجاء إدخال اسم الطعام', 'data': []}, status=400)
        
        from urllib.parse import quote
        encoded_query = quote(query)
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_query}&search_simple=1&action=process&json=1&page_size=20&fields=code,product_name,generic_name,brands,nutriments,image_front_small_url,serving_size"
        
        headers = {'User-Agent': 'LivocareApp/1.0 (https://livocare.onrender.com)'}
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            products = []
            for product in data.get('products', []):
                nutriments = product.get('nutriments', {})
                product_name = product.get('product_name') or product.get('generic_name')
                
                if product_name and len(product_name) > 1:
                    products.append({
                        'id': product.get('code'),
                        'name': product_name,
                        'calories': float(nutriments.get('energy-kcal') or nutriments.get('energy') or 0),
                        'protein': float(nutriments.get('proteins') or 0),
                        'carbs': float(nutriments.get('carbohydrates') or 0),
                        'fat': float(nutriments.get('fat') or 0),
                        'fiber': float(nutriments.get('fiber') or 0),
                        'image': product.get('image_front_small_url'),
                        'brand': product.get('brands')
                    })
            
            return Response({'success': True, 'data': products, 'count': len(products)})
        else:
            return Response({'success': False, 'error': 'فشل في الاتصال بقاعدة البيانات', 'data': []}, status=500)
        
    except Exception as e:
        return Response({'success': False, 'error': str(e), 'data': []}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggest_exercises(request):
    """اقتراح تمارين رياضية"""
    try:
        lang_param = request.query_params.get('lang')
        accept_lang = request.headers.get('Accept-Language', 'ar')
        language = lang_param if lang_param in ['ar', 'en'] else ('en' if accept_lang.startswith('en') else 'ar')
        
        muscle = request.query_params.get('muscle')
        difficulty = request.query_params.get('difficulty')
        
        service = AdvancedHealthAnalytics(request.user, language=language)
        exercises = service.suggest_exercises(muscle, difficulty)
        
        return Response({'success': True, 'data': exercises})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ==============================================================================
# 🤖 الذكاء الاصطناعي والتحليلات
# ==============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_sentiment(request):
    """تحليل المشاعر باستخدام Groq API"""
    try:
        text = request.data.get('text', '')
        if not text:
            return Response({'success': False, 'error': 'الرجاء إدخال نص للتحليل'}, status=400)
        
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(text)
        return Response({'success': True, 'data': result})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_smart_recommendations(request):
    """توصيات ذكية مخصصة للمستخدم"""
    try:
        user = request.user
        latest_health = HealthStatus.objects.filter(user=user).first()
        latest_mood = MoodEntry.objects.filter(user=user).first()
        recent_activities = PhysicalActivity.objects.filter(user=user, start_time__date=date.today()).count()
        
        recommendations = []
        
        if latest_health and latest_health.weight_kg and latest_health.weight_kg > 90:
            recommendations.append({'icon': '⚖️', 'message': 'وزنك أعلى من المعدل. جرب المشي 30 دقيقة يومياً'})
        
        if latest_mood and latest_mood.mood in ['Stressed', 'Anxious', 'Sad']:
            recommendations.append({'icon': '🧘', 'message': 'مزاجك متعب اليوم. جرب تمارين التنفس العميق'})
        
        if recent_activities == 0:
            recommendations.append({'icon': '🚶', 'message': 'لم تمارس أي نشاط اليوم. المشي 10 دقائق مفيد لصحتك'})
        
        return Response({'success': True, 'data': recommendations})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


class ChatLogViewSet(BaseUserViewSet):
    queryset = ChatLog.objects.all()
    serializer_class = ChatLogSerializer
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        message = request.data.get('message', '')
        if not message:
            return Response({'error': 'الرسالة مطلوبة'}, status=400)
        
        user_message = ChatLog.objects.create(user=request.user, sender='User', message_text=message, sentiment_score=0.0)
        
        recent_messages = ChatLog.objects.filter(user=request.user).order_by('timestamp')[:20]
        chat_history = [{'sender': msg.sender, 'message': msg.message_text} for msg in recent_messages]
        
        try:
            llama_service = LlamaService()
            bot_response = llama_service.get_chat_response(message, request.user, chat_history)
        except Exception as e:
            bot_response = f"عذراً {request.user.username}، حدث خطأ غير متوقع."
        
        bot_message = ChatLog.objects.create(user=request.user, sender='Bot', message_text=bot_response, sentiment_score=0.0)
        
        all_messages = ChatLog.objects.filter(user=request.user).order_by('-timestamp')[:50]
        messages_for_display = list(reversed(all_messages))
        serializer = self.get_serializer(messages_for_display, many=True)
        return Response(serializer.data, status=201)


# ==============================================================================
# 🧠 التحليلات المتقدمة
# ==============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_insights(request):
    """تحليلات التغذية المتقدمة"""
    user = request.user
    meals = Meal.objects.filter(user=user)
    
    if not meals.exists():
        return Response({
            'total_meals': 0, 'avg_calories': 0, 'avg_protein': 0, 'avg_carbs': 0, 'avg_fat': 0,
            'total_protein': 0, 'total_carbs': 0, 'total_fat': 0, 'meal_distribution': {},
            'trend': 'insufficient_data', 'recommendations': []
        })
    
    totals = meals.aggregate(
        total_calories=Sum('total_calories'), total_protein=Sum('total_protein'),
        total_carbs=Sum('total_carbs'), total_fat=Sum('total_fat')
    )
    
    total_meals = meals.count()
    avg_calories = (totals['total_calories'] or 0) / total_meals
    
    meal_distribution = meals.values('meal_type').annotate(count=Count('id'))
    distribution_dict = {item['meal_type']: item['count'] for item in meal_distribution}
    
    return Response({
        'total_meals': total_meals,
        'avg_calories': round(avg_calories, 1),
        'avg_protein': round(float(totals['total_protein'] or 0) / total_meals, 1),
        'avg_carbs': round(float(totals['total_carbs'] or 0) / total_meals, 1),
        'avg_fat': round(float(totals['total_fat'] or 0) / total_meals, 1),
        'total_protein': round(float(totals['total_protein'] or 0), 1),
        'total_carbs': round(float(totals['total_carbs'] or 0), 1),
        'total_fat': round(float(totals['total_fat'] or 0), 1),
        'meal_distribution': distribution_dict,
        'trend': 'stable', 'recommendations': []
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_insights(request):
    """تحليلات ذكية متكاملة"""
    user = request.user
    today = timezone.now()
    week_ago = today - timedelta(days=7)
    
    lang = request.GET.get('lang', 'ar')
    is_arabic = lang.startswith('ar')
    
    # بيانات العادات
    habits = HabitDefinition.objects.filter(user=user)
    habit_logs = HabitLog.objects.filter(habit__user=user, log_date__gte=week_ago.date())
    total_habits = habits.count()
    completed_today = habit_logs.filter(log_date=today.date(), is_completed=True).count()
    completion_rate = round((completed_today / total_habits) * 100) if total_habits > 0 else 0
    
    # بيانات النوم
    sleep_data = Sleep.objects.filter(user=user, sleep_start__gte=week_ago)
    avg_sleep = sleep_data.aggregate(Avg('duration_hours'))['duration_hours__avg'] or 0
    
    # بيانات المزاج
    mood_data = MoodEntry.objects.filter(user=user, entry_time__gte=week_ago)
    mood_counts = mood_data.values('mood').annotate(count=Count('mood'))
    dominant_mood = mood_counts.order_by('-count').first()
    
    # بيانات التغذية
    meal_data = Meal.objects.filter(user=user, meal_time__gte=week_ago)
    avg_calories = meal_data.aggregate(Avg('total_calories'))['total_calories__avg'] or 0
    
    # توصيات
    recommendations = []
    
    if avg_sleep < 7:
        recommendations.append({
            'icon': '🌙', 'title': 'نم أكثر لتحسين صحتك' if is_arabic else 'Get Enough Sleep',
            'tips': ['حدد موعداً ثابتاً للنوم' if is_arabic else 'Set a fixed bedtime',
                     'ابتعد عن الشاشات قبل النوم' if is_arabic else 'Avoid screens before sleep'],
            'based_on': '7 أيام' if is_arabic else '7 days', 'improvement_chance': 80
        })
    
    if completion_rate < 50:
        recommendations.append({
            'icon': '💊', 'title': 'التزم بعاداتك اليومية' if is_arabic else 'Stick to Daily Habits',
            'tips': ['ابدأ بعادة صغيرة وسهلة' if is_arabic else 'Start with a small, easy habit'],
            'based_on': 'اليوم' if is_arabic else 'Today', 'improvement_chance': 90
        })
    
    if avg_calories < 1500:
        recommendations.append({
            'icon': '🥗', 'title': 'نظام غذائي متوازن' if is_arabic else 'Balanced Nutrition',
            'tips': ['أضف وجبات خفيفة صحية' if is_arabic else 'Add healthy snacks'],
            'based_on': 'آخر أسبوع' if is_arabic else 'Last week', 'improvement_chance': 85
        })
    
    return Response({
        'success': True,
        'data': {
            'summary': {
                'total_habits': total_habits, 'completed_today': completed_today,
                'completion_rate': completion_rate, 'avg_sleep': round(float(avg_sleep), 1),
                'dominant_mood': dominant_mood['mood'] if dominant_mood else ('غير متوفر' if is_arabic else 'Not available'),
                'avg_calories': round(float(avg_calories))
            },
            'recommendations': recommendations
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def advanced_cross_insights(request):
    """تحليلات متقاطعة متقدمة"""
    try:
        lang_param = request.query_params.get('lang')
        accept_lang = request.headers.get('Accept-Language', 'ar')
        language = lang_param if lang_param in ['ar', 'en'] else ('en' if accept_lang.startswith('en') else 'ar')
        
        engine = HealthInsightsEngine(request.user, language=language)
        data = {
            'energy_consumption': engine.analyze_energy_consumption(),
            'pulse_pressure': engine.analyze_pulse_pressure(),
            'pre_exercise': engine.analyze_pre_exercise_risk(),
            'vital_signs': engine.analyze_vital_signs(),
            'holistic': engine.generate_holistic_recommendations(),
            'predictive': engine.generate_predictive_alerts()
        }
        return Response({'success': True, 'data': data})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cross_insights(request):
    """تحليلات متقاطعة أساسية (للتوافق)"""
    try:
        from .services.cross_insights_service import CrossInsightsService
        service = CrossInsightsService(request.user)
        insights = service.get_all_correlations()
        return Response({'success': True, 'data': insights})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ==============================================================================
# 🔔 الإشعارات (خدمة خارجية)
# ==============================================================================

NOTIFICATION_SERVICE_URL = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'https://notification-service-2xej.onrender.com')


class NotificationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    def _request_to_service(self, endpoint, method='GET', data=None):
        url = f"{NOTIFICATION_SERVICE_URL}/api/{endpoint}"
        payload = data or {}
        payload['user_id'] = self.request.user.id
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=payload, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=payload, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, json=payload, timeout=10)
            else:
                return {'success': False, 'error': f'Method {method} not supported'}
            
            return response.json() if response.status_code == 200 else {'success': False, 'error': f'Service error: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @action(detail=False, methods=['get'])
    def get_all(self, request):
        return Response(self._request_to_service('notifications/', 'GET', {'limit': request.query_params.get('limit', 50)}))
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        return Response(self._request_to_service('notifications/unread-count/', 'GET'))
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        return Response(self._request_to_service(f'notifications/{pk}/mark-read/', 'POST'))
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        return Response(self._request_to_service('notifications/mark-all-read/', 'POST'))
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response(self._request_to_service('notifications/stats/', 'GET'))


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def trigger_notifications(request):
    try:
        url = f"{NOTIFICATION_SERVICE_URL}/api/trigger/"
        response = requests.post(url, timeout=30)
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def push_subscribe(request):
    try:
        subscription = request.data
        if not subscription or not subscription.get('endpoint'):
            return Response({'success': False, 'error': 'بيانات الاشتراك غير صالحة'}, status=400)
        
        request.session['push_subscription'] = subscription
        return Response({'success': True, 'message': 'تم حفظ اشتراك الإشعارات بنجاح'})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_achievements(request):
    """جلب إنجازات المستخدم"""
    return Response({'success': True, 'data': []})


# ==============================================================================
# ⌚ بيانات الساعة الذكية
# ==============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def watch_health_data(request):
    try:
        data = request.data
        heart_rate = data.get('heart_rate') or data.get('heartRate')
        systolic = data.get('systolic_pressure') or data.get('systolic')
        diastolic = data.get('diastolic_pressure') or data.get('diastolic')
        recorded_at = data.get('recorded_at') or data.get('timestamp') or timezone.now()
        
        health_data = HealthStatus.objects.create(
            user=request.user, heart_rate=heart_rate,
            systolic_pressure=systolic, diastolic_pressure=diastolic, recorded_at=recorded_at
        )
        
        return Response({'success': True, 'data': {'id': health_data.id}})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def watch_history(request):
    try:
        data = HealthStatus.objects.filter(user=request.user).order_by('-recorded_at')[:50]
        result = [{'id': item.id, 'heart_rate': item.heart_rate, 'systolic_pressure': item.systolic_pressure,
                   'diastolic_pressure': item.diastolic_pressure, 'recorded_at': item.recorded_at.isoformat()}
                  for item in data]
        return Response({'success': True, 'data': result})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ==============================================================================
# 🔐 المصادقة
# ==============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def google_auth(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        name = data.get('name', '')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': email.split('@')[0], 'first_name': name.split()[0] if name else ''}
        )
        
        refresh = RefreshToken.for_user(user)
        return JsonResponse({'access': str(refresh.access_token), 'refresh': str(refresh)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==============================================================================
# 📷 مسح الباركود
# ==============================================================================

@csrf_exempt
@api_view(['POST'])
def scan_barcode(request):
    try:
        data = json.loads(request.body)
        camera_url = os.environ.get('CAMERA_SERVICE_URL', 'https://camera-service-fag3.onrender.com')
        response = requests.post(f"{camera_url}/scan-barcode", json={'image': data.get('image', '')}, timeout=10)
        return JsonResponse(response.json(), status=response.status_code)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ==============================================================================
# 🩺 الأدوية
# ==============================================================================

class OpenFDAService:
    BASE_URL = "https://api.fda.gov/drug"
    
    def search_by_brand_name(self, brand_name, limit=10):
        params = {'search': f'openfda.brand_name.exact:"{brand_name}"', 'limit': limit}
        try:
            response = requests.get(f"{self.BASE_URL}/drugsfda.json", params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = []
                for drug in data.get('results', []):
                    openfda = drug.get('openfda', {})
                    results.append({
                        'brand_name': openfda.get('brand_name', [''])[0] if openfda.get('brand_name') else '',
                        'generic_name': openfda.get('generic_name', [''])[0] if openfda.get('generic_name') else '',
                        'manufacturer': openfda.get('manufacturer_name', [''])[0] if openfda.get('manufacturer_name') else '',
                    })
                return results
        except Exception:
            pass
        return []


fda_service = OpenFDAService()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_medication(request):
    query = request.query_params.get('q', '').strip()
    if not query:
        return Response({'success': False, 'error': 'الرجاء إدخال اسم الدواء', 'results': []}, status=400)
    
    results = fda_service.search_by_brand_name(query)
    return Response({'success': True, 'results': results, 'count': len(results)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_medication_details(request, medication_id):
    return Response({'success': False, 'error': 'قيد التطوير'}, status=501)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_medications(request):
    return Response({'success': True, 'data': [], 'count': 0})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_user_medication(request):
    return Response({'success': False, 'error': 'قيد التطوير'}, status=501)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_medication(request, user_med_id):
    return Response({'success': False, 'error': 'قيد التطوير'}, status=501)


# ==============================================================================
# 🧪 دوال اختبارية
# ==============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def test_websocket(request):
    return Response({'success': True, 'message': 'WebSocket API is working', 'status': 'ok'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_notifications_now(request):
    from main.services.notification_service import NotificationService
    try:
        count = NotificationService.generate_all_notifications(request.user)
        return Response({'success': True, 'message': f'✅ تم إنشاء {count} إشعار جديد', 'count': count})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)