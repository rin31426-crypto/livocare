from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
# main/services/llama_service.py
import requests
from django.conf import settings
import time
from ..models import HealthStatus, MoodEntry, Sleep, Meal, PhysicalActivity

class LlamaService:
    def __init__(self):
        # إعدادات API (Groq)
        self.api_key = getattr(settings, 'GROQ_API_KEY', None)
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_model = "llama-3.1-8b-instant"
        
        # إعدادات المحلي (LM Studio)
        self.local_url = "http://localhost:1234/v1/chat/completions"
        self.local_model = "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"
        
        self.use_api = True
    
    def get_chat_response(self, message, user, chat_history=[]):
        """يحاول API أولاً، ثم المحلي، ثم الرد الاحتياطي"""
        
        # ========== جمع بيانات المستخدم الحقيقية ==========
        user_data = self._collect_user_data(user)
        
        # بناء الرسائل مع دمج بيانات المستخدم
        messages = self._build_messages(message, user, chat_history, user_data)
        
        # 1. جرب API
        if self.use_api and self.api_key:
            response = self._try_api(messages)
            if response:
                return response
            else:
                print("⚠️ API failed, switching to local mode")
                self.use_api = False
        
        # 2. جرب المحلي
        response = self._try_local(messages)
        if response:
            return response
        
        # 3. الرد الاحتياطي الذكي (باستخدام بيانات المستخدم)
        return self._smart_fallback(message, user, user_data)
    
    def _collect_user_data(self, user):
        """جمع كل بيانات المستخدم من قاعدة البيانات"""
        user_data = {}
        
        # آخر البيانات الصحية
        last_health = HealthStatus.objects.filter(user=user).order_by('-recorded_at').first()
        if last_health:
            user_data['weight'] = last_health.weight_kg
            user_data['blood_pressure'] = f"{last_health.systolic_pressure}/{last_health.diastolic_pressure}" if last_health.systolic_pressure else None
            user_data['glucose'] = last_health.blood_glucose
        
        # آخر مزاج
        last_mood = MoodEntry.objects.filter(user=user).order_by('-entry_time').first()
        if last_mood:
            user_data['mood'] = last_mood.mood
        
        # متوسط النوم آخر 7 أيام
        week_ago = timezone.now() - timedelta(days=7)
        sleeps = Sleep.objects.filter(user=user, sleep_start__gte=week_ago)
        if sleeps.exists():
            total_sleep = 0
            count = 0
            for sleep in sleeps:
                if sleep.sleep_start and sleep.sleep_end:
                    duration = (sleep.sleep_end - sleep.sleep_start).seconds / 3600
                    if duration < 24:
                        total_sleep += duration
                        count += 1
            user_data['avg_sleep'] = round(total_sleep / count, 1) if count > 0 else None
        
        # سعرات اليوم
        today = timezone.now().date()
        today_meals = Meal.objects.filter(user=user, meal_time__date=today)
        user_data['calories_today'] = today_meals.aggregate(Sum('total_calories'))['total_calories__sum'] or 0
        
        # عدد الأنشطة هذا الأسبوع
        activities = PhysicalActivity.objects.filter(user=user, start_time__gte=week_ago)
        user_data['activities_count'] = activities.count()
        
        return user_data
    
    def _build_messages(self, message, user, chat_history, user_data):
        """بناء رسائل المحادثة مع دمج بيانات المستخدم"""
        
        # بناء سياق المستخدم
        user_context = f"""معلومات عن المستخدم {user.username}:
- الوقت: {time.strftime('%Y-%m-%d %H:%M')}"""

        if user_data.get('weight'):
            user_context += f"\n- الوزن: {user_data['weight']} كجم"
        if user_data.get('blood_pressure'):
            user_context += f"\n- ضغط الدم: {user_data['blood_pressure']}"
        if user_data.get('glucose'):
            user_context += f"\n- السكر: {user_data['glucose']}"
        if user_data.get('mood'):
            user_context += f"\n- آخر مزاج: {user_data['mood']}"
        if user_data.get('avg_sleep'):
            user_context += f"\n- متوسط النوم: {user_data['avg_sleep']} ساعات"
        if user_data.get('calories_today'):
            user_context += f"\n- سعرات اليوم: {user_data['calories_today']}"
        if user_data.get('activities_count'):
            user_context += f"\n- أنشطة هذا الأسبوع: {user_data['activities_count']}"
        
        system_prompt = f"""أنت "Livocare AI" - مساعد صحي ذكي ومتعاطف.

{user_context}

تعليمات مهمة:
1️⃣ استخدم معلومات المستخدم الحقيقية في ردودك
2️⃣ إذا سأل عن وزنه، أعطه وزنه الحقيقي
3️⃣ إذا سأل عن نومه، أخبره بمتوسط نومه
4️⃣ كن ودوداً ومشجعاً
5️⃣ تحدث باللغة العربية الفصحى البسيطة
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # إضافة تاريخ المحادثة
        for msg in chat_history[-8:]:
            role = "user" if msg['sender'] == 'User' else "assistant"
            messages.append({"role": role, "content": msg['message']})
        
        messages.append({"role": "user", "content": message})
        return messages
    
    def _try_api(self, messages):
        """محاولة استخدام Groq API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.api_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        
        try:
            print("🚀 Trying Groq API...")
            response = requests.post(
                self.api_url, 
                json=payload, 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                print(f"❌ API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ API Exception: {e}")
            return None
    
    def _try_local(self, messages):
        """محاولة استخدام LM Studio المحلي"""
        payload = {
            "model": self.local_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        
        try:
            print("🏠 Trying local Llama...")
            response = requests.post(
                self.local_url, 
                json=payload, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                return None
                
        except:
            return None
    
    def _smart_fallback(self, message, user, user_data):
        """رد احتياطي ذكي باستخدام بيانات المستخدم"""
        message_lower = message.lower()
        
        # ردود ذكية باستخدام البيانات الحقيقية
        if 'وزن' in message_lower:
            if user_data.get('weight'):
                return f"⚖️ {user.username}، آخر وزن لك هو **{user_data['weight']} كجم**. هل تريد نصائح للوصول لوزن مثالي؟"
            return f"⚖️ {user.username}، لم تسجل أي وزن بعد. يمكنك إضافة وزنك في قسم الصحة الحيوية."
        
        if 'نوم' in message_lower:
            if user_data.get('avg_sleep'):
                return f"🌙 {user.username}، متوسط نومك خلال الأسبوع الماضي هو **{user_data['avg_sleep']} ساعات**. هل تريد نصائح لتحسين النوم؟"
            return f"🌙 {user.username}، لم تسجل أي نوم بعد. يمكنك تتبع نومك في قسم النوم."
        
        if 'مزاج' in message_lower:
            if user_data.get('mood'):
                mood_messages = {
                    'excellent': 'ممتاز! استمر في هذا النشاط',
                    'good': 'جيد، حافظ على روتينك',
                    'neutral': 'مزاجك محايد، جرب نشاطًا جديدًا',
                    'stressed': 'يبدو أنك متوتر. جرب التنفس العميق',
                    'anxious': 'القلق طبيعي، خذ قسطًا من الراحة',
                    'sad': 'الأيام الصعبة تمر، تحدث مع صديق',
                }
                advice = mood_messages.get(user_data['mood'], '')
                return f"😊 {user.username}، آخر مزاج لك كان **{user_data['mood']}**. {advice}"
            return f"😊 {user.username}، لم تسجل أي مزاج بعد. كيف تشعر اليوم؟"
        
        if 'سعرات' in message_lower or 'اكل' in message_lower:
            if user_data.get('calories_today'):
                return f"🥗 {user.username}، تناولت اليوم **{user_data['calories_today']} سعرة**. هل تريد معرفة إذا كان هذا مناسباً؟"
            return f"🥗 {user.username}، لم تسجل أي وجبات اليوم. يمكنك تسجيل وجباتك في قسم التغذية."
        
        # رد افتراضي مع ملخص سريع
        summary = f"""👋 مرحباً {user.username}! 

**ملخص حالتك الصحية:**"""
        
        if user_data.get('weight'):
            summary += f"\n⚖️ الوزن: {user_data['weight']} كجم"
        if user_data.get('avg_sleep'):
            summary += f"\n🌙 متوسط النوم: {user_data['avg_sleep']} ساعات"
        if user_data.get('mood'):
            summary += f"\n😊 آخر مزاج: {user_data['mood']}"
        if user_data.get('calories_today'):
            summary += f"\n🥗 سعرات اليوم: {user_data['calories_today']}"
        
        summary += "\n\n**كيف يمكنني مساعدتك؟** 😊"
        return summary