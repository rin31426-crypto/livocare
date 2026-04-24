# main/services/gemini_service.py
from google import genai
from django.conf import settings
from django.db import models  # ✅ أضف هذا السطر
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
        
        # سعرات اليوم - ✅ استخدم models.Sum بشكل صحيح
        today = datetime.now().date()
        from ..models import Meal
        calories_today = Meal.objects.filter(user=user, meal_time__date=today).aggregate(
            models.Sum('total_calories')
        )['total_calories__sum'] or 0
        user_data['calories_today'] = calories_today
        
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