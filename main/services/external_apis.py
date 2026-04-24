# main/services/external_apis.py
from django.conf import settings
import requests
import json

class APIConfig:
    """تكوين APIs الخارجية - جلب المفاتيح من settings.py"""
    
    # OpenWeather API
    WEATHER_API_KEY = settings.OPENWEATHER_API_KEY
    WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5"
    
    # OpenFoodFacts - مجاني تماماً
    OPENFOODFACTS_ENABLED = getattr(settings, 'OPENFOODFACTS_ENABLED', True)
    OPENFOODFACTS_BASE_URL = "https://world.openfoodfacts.org"
    
    # RapidAPI
    RAPIDAPI_KEY = getattr(settings, 'RAPIDAPI_KEY', '')
    RAPIDAPI_HOST = "nutrition-tracker-api.p.rapidapi.com"
    
    # Google Maps
    GOOGLE_MAPS_KEY = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')

    @staticmethod
    def _get_language_text(ar_text, en_text, is_arabic=True):
        """اختيار النص حسب اللغة"""
        return ar_text if is_arabic else en_text

    @staticmethod
    def get_weather(city, language='ar'):
        """جلب بيانات الطقس من OpenWeather"""
        is_arabic = language == 'ar'
        
        try:
            url = f"{APIConfig.WEATHER_BASE_URL}/weather"
            params = {
                'q': city,
                'appid': APIConfig.WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ar' if is_arabic else 'en'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # استخراج الإرشادات بناءً على الطقس
                temp = data['main']['temp']
                weather_main = data['weather'][0]['main']
                
                recommendation = ""
                if temp > 35:
                    recommendation = APIConfig._get_language_text(
                        "الجو حار جداً، اشرب الكثير من الماء وتجنب التعرض المباشر للشمس",
                        "Very hot weather, drink plenty of water and avoid direct sunlight",
                        is_arabic
                    )
                elif temp > 30:
                    recommendation = APIConfig._get_language_text(
                        "الجو حار، احرص على ترطيب جسمك",
                        "Hot weather, stay hydrated",
                        is_arabic
                    )
                elif temp < 10:
                    recommendation = APIConfig._get_language_text(
                        "الجو بارد، ارتد ملابس دافئة واحصل على قسط كاف من النوم",
                        "Cold weather, wear warm clothes and get enough sleep",
                        is_arabic
                    )
                elif 'rain' in weather_main.lower():
                    recommendation = APIConfig._get_language_text(
                        "الجو ممطر، احرص على أخذ مظلتك وارتداء ملابس مناسبة",
                        "Rainy weather, don't forget your umbrella and wear appropriate clothing",
                        is_arabic
                    )
                else:
                    recommendation = APIConfig._get_language_text(
                        "طقس معتدل، وقت مناسب للمشي والأنشطة الخارجية",
                        "Mild weather, good time for walking and outdoor activities",
                        is_arabic
                    )
                
                return {
                    'success': True,
                    'city': data['name'],
                    'temperature': round(temp),
                    'feels_like': round(data['main']['feels_like']),
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon'],
                    'wind_speed': data['wind']['speed'],
                    'recommendation': recommendation
                }
            else:
                return {
                    'success': False,
                    'error': APIConfig._get_language_text(
                        'تعذر جلب بيانات الطقس',
                        'Unable to fetch weather data',
                        is_arabic
                    ),
                    'data': APIConfig._get_mock_weather(city, is_arabic)
                }
                
        except Exception as e:
            print(f"Weather API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': APIConfig._get_mock_weather(city, is_arabic)
            }
    
    @staticmethod
    def _get_mock_weather(city, is_arabic=True):
        """بيانات تجريبية للطقس"""
        return {
            'city': city,
            'temperature': 25,
            'feels_like': 24,
            'humidity': 60,
            'description': APIConfig._get_language_text('سماء صافية', 'Clear sky', is_arabic),
            'icon': '01d',
            'wind_speed': 3.5,
            'recommendation': APIConfig._get_language_text(
                'طقس معتدل، وقت مناسب للمشي والأنشطة الخارجية',
                'Mild weather, good time for walking and outdoor activities',
                is_arabic
            )
        }
    
    @staticmethod
    def search_food_openfoodfacts(query, language='ar'):
        """البحث عن الطعام باستخدام OpenFoodFacts API"""
        is_arabic = language == 'ar'
        
        try:
            url = f"{APIConfig.OPENFOODFACTS_BASE_URL}/cgi/search.pl"
            
            params = {
                'search_terms': query,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 8,
                'fields': 'product_name,nutriments,image_url,categories,code'
            }
            
            print(f"Searching OpenFoodFacts for: {query}")
            response = requests.get(url, params=params, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                results = []
                for product in products[:6]:
                    nutriments = product.get('nutriments', {})
                    
                    # استخراج القيم الغذائية
                    calories = nutriments.get('energy-kcal_100g') or nutriments.get('energy_100g', 0)
                    if calories and calories > 1000:
                        calories = calories / 4.184
                    
                    name = product.get('product_name', '')
                    if not name or name == '':
                        name = query
                    
                    image = product.get('image_url')
                    
                    results.append({
                        'name': name,
                        'calories': round(calories) if calories else 100,
                        'protein': round(nutriments.get('proteins_100g', 5), 1),
                        'carbs': round(nutriments.get('carbohydrates_100g', 10), 1),
                        'fat': round(nutriments.get('fat_100g', 3), 1),
                        'fiber': round(nutriments.get('fiber_100g', 1), 1),
                        'image': image
                    })
                
                print(f"Found {len(results)} results from OpenFoodFacts")
                return results
            
            print(f"OpenFoodFacts returned status code: {response.status_code}")
            return []
            
        except requests.exceptions.Timeout:
            print("OpenFoodFacts timeout after 25 seconds")
            return []
        except Exception as e:
            print(f"OpenFoodFacts error: {e}")
            return []
    
    @staticmethod
    def search_food_mock(query, language='ar'):
        """بيانات تجريبية - تستخدم كبديل إذا فشل API"""
        query_lower = query.lower()
        is_arabic = language == 'ar'
        
        # قائمة الأطعمة بالعربية
        mock_database_ar = {
            'رز': [
                {
                    'name': 'أرز أبيض مطبوخ',
                    'calories': 130,
                    'protein': 2.7,
                    'carbs': 28,
                    'fat': 0.3,
                    'fiber': 0.4,
                    'image': None
                },
                {
                    'name': 'أرز بسمتي',
                    'calories': 150,
                    'protein': 3.5,
                    'carbs': 32,
                    'fat': 0.5,
                    'fiber': 0.6,
                    'image': None
                }
            ],
            'تفاح': [
                {
                    'name': 'تفاح أحمر',
                    'calories': 52,
                    'protein': 0.3,
                    'carbs': 14,
                    'fat': 0.2,
                    'fiber': 2.4,
                    'image': None
                }
            ],
            'موز': [
                {
                    'name': 'موز',
                    'calories': 89,
                    'protein': 1.1,
                    'carbs': 23,
                    'fat': 0.3,
                    'fiber': 2.6,
                    'image': None
                }
            ],
            'دجاج': [
                {
                    'name': 'دجاج مشوي',
                    'calories': 165,
                    'protein': 31,
                    'carbs': 0,
                    'fat': 3.6,
                    'fiber': 0,
                    'image': None
                }
            ],
            'لحم': [
                {
                    'name': 'ستيك لحم',
                    'calories': 271,
                    'protein': 25,
                    'carbs': 0,
                    'fat': 19,
                    'fiber': 0,
                    'image': None
                }
            ],
            'خبز': [
                {
                    'name': 'خبز أبيض',
                    'calories': 265,
                    'protein': 9,
                    'carbs': 49,
                    'fat': 3.2,
                    'fiber': 2.7,
                    'image': None
                },
                {
                    'name': 'خبز أسمر',
                    'calories': 247,
                    'protein': 13,
                    'carbs': 41,
                    'fat': 4.2,
                    'fiber': 6.8,
                    'image': None
                }
            ],
            'بيض': [
                {
                    'name': 'بيض مسلوق',
                    'calories': 155,
                    'protein': 13,
                    'carbs': 1.1,
                    'fat': 11,
                    'fiber': 0,
                    'image': None
                }
            ],
            'لبن': [
                {
                    'name': 'لبن كامل الدسم',
                    'calories': 61,
                    'protein': 3.3,
                    'carbs': 4.8,
                    'fat': 3.3,
                    'fiber': 0,
                    'image': None
                }
            ],
            'زبادي': [
                {
                    'name': 'زبادي كامل الدسم',
                    'calories': 61,
                    'protein': 3.5,
                    'carbs': 4.7,
                    'fat': 3.3,
                    'fiber': 0,
                    'image': None
                }
            ]
        }
        
        # قائمة الأطعمة بالإنجليزية
        mock_database_en = {
            'rice': [
                {
                    'name': 'White Rice (cooked)',
                    'calories': 130,
                    'protein': 2.7,
                    'carbs': 28,
                    'fat': 0.3,
                    'fiber': 0.4,
                    'image': None
                },
                {
                    'name': 'Basmati Rice',
                    'calories': 150,
                    'protein': 3.5,
                    'carbs': 32,
                    'fat': 0.5,
                    'fiber': 0.6,
                    'image': None
                }
            ],
            'apple': [
                {
                    'name': 'Red Apple',
                    'calories': 52,
                    'protein': 0.3,
                    'carbs': 14,
                    'fat': 0.2,
                    'fiber': 2.4,
                    'image': None
                }
            ],
            'banana': [
                {
                    'name': 'Banana',
                    'calories': 89,
                    'protein': 1.1,
                    'carbs': 23,
                    'fat': 0.3,
                    'fiber': 2.6,
                    'image': None
                }
            ],
            'chicken': [
                {
                    'name': 'Grilled Chicken',
                    'calories': 165,
                    'protein': 31,
                    'carbs': 0,
                    'fat': 3.6,
                    'fiber': 0,
                    'image': None
                }
            ],
            'meat': [
                {
                    'name': 'Beef Steak',
                    'calories': 271,
                    'protein': 25,
                    'carbs': 0,
                    'fat': 19,
                    'fiber': 0,
                    'image': None
                }
            ],
            'bread': [
                {
                    'name': 'White Bread',
                    'calories': 265,
                    'protein': 9,
                    'carbs': 49,
                    'fat': 3.2,
                    'fiber': 2.7,
                    'image': None
                },
                {
                    'name': 'Whole Wheat Bread',
                    'calories': 247,
                    'protein': 13,
                    'carbs': 41,
                    'fat': 4.2,
                    'fiber': 6.8,
                    'image': None
                }
            ],
            'egg': [
                {
                    'name': 'Boiled Egg',
                    'calories': 155,
                    'protein': 13,
                    'carbs': 1.1,
                    'fat': 11,
                    'fiber': 0,
                    'image': None
                }
            ],
            'milk': [
                {
                    'name': 'Whole Milk',
                    'calories': 61,
                    'protein': 3.3,
                    'carbs': 4.8,
                    'fat': 3.3,
                    'fiber': 0,
                    'image': None
                }
            ],
            'yogurt': [
                {
                    'name': 'Whole Yogurt',
                    'calories': 61,
                    'protein': 3.5,
                    'carbs': 4.7,
                    'fat': 3.3,
                    'fiber': 0,
                    'image': None
                }
            ]
        }
        
        mock_database = mock_database_ar if is_arabic else mock_database_en
        
        for key in mock_database:
            if key in query_lower:
                return mock_database[key]
        
        # إذا لم يتم العثور على تطابق
        default_name = query if is_arabic else query
        return [
            {
                'name': default_name,
                'calories': 150,
                'protein': 8,
                'carbs': 20,
                'fat': 5,
                'fiber': 2,
                'image': None
            }
        ]


# main/services/gemini_service.py
from google import genai
from django.conf import settings
from ..models import HealthStatus, MoodEntry, Sleep, PhysicalActivity, Meal
from datetime import datetime, timedelta

class GeminiService:
    def __init__(self, language='ar'):
        # 👇 التهيئة الجديدة للمكتبة
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"
        self.language = language
        self.is_arabic = language == 'ar'
    
    def get_user_language(self, user):
        """استرجاع لغة المستخدم"""
        try:
            if hasattr(user, 'profile') and user.profile.language:
                return user.profile.language
        except:
            pass
        return self.language
    
    def get_chat_response(self, message, user, chat_history=[]):
        # تحديد لغة المستخدم
        user_lang = self.get_user_language(user)
        self.is_arabic = user_lang == 'ar'
        self.language = user_lang
        
        # جمع بيانات المستخدم
        user_data = self._collect_user_data(user)
        
        # بناء السياق
        context = self._build_context(user_data, chat_history)
        
        # إنشاء prompt
        prompt = self._build_prompt(message, user, user_data, chat_history)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return self._fallback_response(message, user_data)
    
    def _collect_user_data(self, user):
        """جمع كل بيانات المستخدم من قاعدة البيانات"""
        user_data = {
            'weight': None,
            'blood_pressure': None,
            'glucose': None,
            'heart_rate': None,
            'spo2': None,
            'mood': None,
            'avg_sleep': None,
            'activities_count': 0,
            'calories_today': 0,
            'habits_completed': 0
        }
        
        # آخر البيانات الصحية
        last_health = HealthStatus.objects.filter(user=user).order_by('-recorded_at').first()
        if last_health:
            user_data['weight'] = last_health.weight_kg
            if last_health.systolic_pressure and last_health.diastolic_pressure:
                user_data['blood_pressure'] = f"{last_health.systolic_pressure}/{last_health.diastolic_pressure}"
            user_data['glucose'] = last_health.blood_glucose
            user_data['heart_rate'] = last_health.heart_rate
            user_data['spo2'] = last_health.spo2
        
        # آخر مزاج
        last_mood = MoodEntry.objects.filter(user=user).order_by('-entry_time').first()
        if last_mood:
            user_data['mood'] = last_mood.mood
        
        # متوسط النوم آخر 7 أيام
        week_ago = datetime.now() - timedelta(days=7)
        sleeps = Sleep.objects.filter(user=user, sleep_start__gte=week_ago)
        if sleeps.exists():
            total_sleep = 0
            count = 0
            for sleep in sleeps:
                if sleep.sleep_start and sleep.sleep_end:
                    duration = (sleep.sleep_end - sleep.sleep_start).seconds / 3600
                    if 0 < duration < 24:
                        total_sleep += duration
                        count += 1
            user_data['avg_sleep'] = round(total_sleep / count, 1) if count > 0 else None
        
        # سعرات اليوم
        today = datetime.now().date()
        today_meals = Meal.objects.filter(user=user, meal_time__date=today)
        user_data['calories_today'] = today_meals.aggregate(models.Sum('total_calories'))['total_calories__sum'] or 0
        
        # عدد الأنشطة هذا الأسبوع
        activities = PhysicalActivity.objects.filter(user=user, start_time__gte=week_ago)
        user_data['activities_count'] = activities.count()
        
        # عدد العادات المنجزة اليوم
        from ..models import HabitLog
        today_logs = HabitLog.objects.filter(user=user, log_date=today, is_completed=True)
        user_data['habits_completed'] = today_logs.count()
        
        return user_data
    
    def _build_context(self, user_data, chat_history):
        """بناء سياق المحادثة"""
        if self.is_arabic:
            context = f"""معلومات المستخدم:
- الوزن: {user_data['weight'] or 'غير مسجل'} كجم
- ضغط الدم: {user_data['blood_pressure'] or 'غير مسجل'} mmHg
- السكر: {user_data['glucose'] or 'غير مسجل'} mg/dL
- نبضات القلب: {user_data['heart_rate'] or 'غير مسجل'} BPM
- الأكسجين: {user_data['spo2'] or 'غير مسجل'}%
- آخر مزاج: {user_data['mood'] or 'غير مسجل'}
- متوسط النوم: {user_data['avg_sleep'] or 'غير مسجل'} ساعات
- سعرات اليوم: {user_data['calories_today']} سعرة
- أنشطة هذا الأسبوع: {user_data['activities_count']}
- عادات منجزة اليوم: {user_data['habits_completed']}"""
        else:
            context = f"""User information:
- Weight: {user_data['weight'] or 'Not recorded'} kg
- Blood pressure: {user_data['blood_pressure'] or 'Not recorded'} mmHg
- Glucose: {user_data['glucose'] or 'Not recorded'} mg/dL
- Heart rate: {user_data['heart_rate'] or 'Not recorded'} BPM
- Oxygen level: {user_data['spo2'] or 'Not recorded'}%
- Last mood: {user_data['mood'] or 'Not recorded'}
- Average sleep: {user_data['avg_sleep'] or 'Not recorded'} hours
- Today's calories: {user_data['calories_today']}
- Activities this week: {user_data['activities_count']}
- Habits completed today: {user_data['habits_completed']}"""
        
        return context
    
    def _format_history(self, chat_history):
        """تنسيق تاريخ المحادثة"""
        if not chat_history:
            return "لا توجد محادثة سابقة" if self.is_arabic else "No previous conversation"
        
        formatted = []
        for msg in chat_history[-6:]:
            sender = "المستخدم" if msg['sender'] == 'User' else "المساعد"
            formatted.append(f"{sender}: {msg['message']}")
        
        return "\n".join(formatted)
    
    def _build_prompt(self, message, user, user_data, chat_history):
        """بناء الـ prompt الكامل"""
        
        if self.is_arabic:
            return f"""أنت مساعد صحي ذكي اسمك "LivoCare AI". 

{self._build_context(user_data, chat_history)}

تاريخ المحادثة:
{self._format_history(chat_history)}

المستخدم {user.username} يقول: {message}

تعليمات مهمة:
1️⃣ استخدم معلومات المستخدم الحقيقية في ردودك
2️⃣ إذا سأل عن وزنه، أعطه وزنه الحقيقي
3️⃣ إذا سأل عن نومه، أخبره بمتوسط نومه الحقيقي
4️⃣ كن ودوداً ومشجعاً
5️⃣ قدم نصائح عملية قابلة للتنفيذ
6️⃣ تحدث باللغة العربية الفصحى البسيطة

الرد:"""
        
        else:
            return f"""You are a smart health assistant named "LivoCare AI".

{self._build_context(user_data, chat_history)}

Conversation history:
{self._format_history(chat_history)}

User {user.username} says: {message}

Important instructions:
1️⃣ Use the user's real information in your responses
2️⃣ If asked about weight, give their real weight
3️⃣ If asked about sleep, tell them their real average sleep
4️⃣ Be friendly and encouraging
5️⃣ Provide practical, actionable advice
6️⃣ Speak in simple, clear English

Response:"""
    
    def _fallback_response(self, message, user_data):
        """رد احتياطي ذكي باستخدام بيانات المستخدم"""
        message_lower = message.lower()
        
        if self.is_arabic:
            if 'وزن' in message_lower:
                if user_data.get('weight'):
                    return f"⚖️ وزنك الحالي هو {user_data['weight']} كجم. هل تريد نصائح للوصول لوزن مثالي؟"
                return "⚖️ لم تسجل وزنك بعد. يمكنك إضافته في قسم الصحة الحيوية."
            
            if 'نوم' in message_lower:
                if user_data.get('avg_sleep'):
                    return f"🌙 متوسط نومك خلال الأسبوع الماضي هو {user_data['avg_sleep']} ساعات. هل تريد نصائح لتحسين نومك؟"
                return "🌙 لم تسجل أي نوم بعد. يمكنك تتبع نومك في قسم النوم."
            
            if 'مزاج' in message_lower:
                if user_data.get('mood'):
                    return f"😊 آخر مزاج لك كان {user_data['mood']}. كيف تشعر اليوم؟"
                return "😊 لم تسجل أي مزاج بعد. كيف تشعر اليوم؟"
            
            # رد افتراضي
            return f"""👋 مرحباً! كيف يمكنني مساعدتك اليوم؟

💡 يمكنك سؤالي عن:
- وزنك الحالي
- نومك المتوسط
- حالتك المزاجية
- نصائح صحية عامة

أنا هنا لمساعدتك في رحلتك الصحية! 😊"""
        
        else:
            if 'weight' in message_lower:
                if user_data.get('weight'):
                    return f"⚖️ Your current weight is {user_data['weight']} kg. Would you like tips for reaching your ideal weight?"
                return "⚖️ You haven't recorded your weight yet. You can add it in the health section."
            
            if 'sleep' in message_lower:
                if user_data.get('avg_sleep'):
                    return f"🌙 Your average sleep over the past week is {user_data['avg_sleep']} hours. Would you like tips to improve your sleep?"
                return "🌙 You haven't recorded any sleep yet. You can track your sleep in the sleep section."
            
            if 'mood' in message_lower:
                if user_data.get('mood'):
                    return f"😊 Your last recorded mood was {user_data['mood']}. How are you feeling today?"
                return "😊 You haven't recorded any mood yet. How are you feeling today?"
            
            # Default response
            return f"""👋 Hello! How can I help you today?

💡 You can ask me about:
- Your current weight
- Your average sleep
- Your mood
- General health tips

I'm here to help you on your health journey! 😊"""