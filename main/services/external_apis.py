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
    def get_weather(city):
        """جلب بيانات الطقس من OpenWeather"""
        try:
            url = f"{APIConfig.WEATHER_BASE_URL}/weather"
            params = {
                'q': city,
                'appid': APIConfig.WEATHER_API_KEY,
                'units': 'metric',
                'lang': 'ar'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # استخراج الإرشادات بناءً على الطقس
                temp = data['main']['temp']
                weather_main = data['weather'][0]['main']
                
                recommendation = ""
                if temp > 35:
                    recommendation = "الجو حار جداً، اشرب الكثير من الماء وتجنب التعرض المباشر للشمس"
                elif temp > 30:
                    recommendation = "الجو حار، احرص على ترطيب جسمك"
                elif temp < 10:
                    recommendation = "الجو بارد، ارتد ملابس دافئة واحصل على قسط كاف من النوم"
                elif 'rain' in weather_main.lower():
                    recommendation = "الجو ممطر، احرص على أخذ مظلتك وارتداء ملابس مناسبة"
                else:
                    recommendation = "طقس معتدل، وقت مناسب للمشي والأنشطة الخارجية"
                
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
                    'error': 'تعذر جلب بيانات الطقس',
                    'data': APIConfig._get_mock_weather(city)
                }
                
        except Exception as e:
            print(f"Weather API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': APIConfig._get_mock_weather(city)
            }
    
    @staticmethod
    def _get_mock_weather(city):
        """بيانات تجريبية للطقس"""
        return {
            'city': city,
            'temperature': 25,
            'feels_like': 24,
            'humidity': 60,
            'description': 'سماء صافية',
            'icon': '01d',
            'wind_speed': 3.5,
            'recommendation': 'طقس معتدل، وقت مناسب للمشي والأنشطة الخارجية'
        }
    
    @staticmethod
    def search_food_openfoodfacts(query):
        """البحث عن الطعام باستخدام OpenFoodFacts API"""
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
    def search_food_mock(query):
        """بيانات تجريبية - تستخدم كبديل إذا فشل API"""
        query_lower = query.lower()
        
        mock_database = {
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
            'rice': [
                {
                    'name': 'White Rice (cooked)',
                    'calories': 130,
                    'protein': 2.7,
                    'carbs': 28,
                    'fat': 0.3,
                    'fiber': 0.4,
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
            ]
        }
        
        for key in mock_database:
            if key in query_lower:
                return mock_database[key]
        
        return [
            {
                'name': query,
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
from ..models import HealthStatus, MoodEntry, Sleep
from datetime import datetime, timedelta

class GeminiService:
    def __init__(self):
        # 👇 التهيئة الجديدة للمكتبة
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"  # أو gemini-1.5-pro حسب تفضيلك
    
    def get_chat_response(self, message, user, chat_history=[]):
        # جمع بيانات المستخدم (نفس الكود)
        user_data = self._collect_user_data(user)
        
        # بناء السياق (نفس الكود)
        context = self._build_context(user_data, chat_history)
        
        # إنشاء prompt (نفس الكود)
        prompt = f"""أنت مساعد صحي ذكي اسمك "Livocare AI". 
معلومات المستخدم الحالية:
- الاسم: {user.username}
- آخر وزن: {user_data['weight']} كجم
- آخر ضغط: {user_data['blood_pressure']}
- آخر سكر: {user_data['glucose']}
- آخر مزاج: {user_data['mood']}
- متوسط النوم: {user_data['avg_sleep']} ساعات
- عدد الأنشطة هذا الأسبوع: {user_data['activities_count']}

تاريخ المحادثة:
{self._format_history(chat_history)}

المستخدم الآن: {message}

قم بالرد بطريقة طبيعية ومفيدة. استخدم معلومات المستخدم الحقيقية في ردودك.
إذا سأل عن معدل النوم، أعطه متوسط نومه الحقيقي.
إذا سأل عن الوزن، أخبره بوزنه الحقيقي.
كن ودوداً ومشجعاً.
"""
        
        try:
            # 👇 طريقة الاستدعاء الجديدة
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return self._fallback_response(message, user_data)
    
    # ... باقي الدوال (_collect_user_data, _build_context, _format_history, _fallback_response) كما هي دون تغيير
    # انسخها من ملفك الحالي