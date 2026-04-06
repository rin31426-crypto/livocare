# main/services/notification_service.py
from django.utils import timezone
from datetime import timedelta
from main.models import Notification, HealthStatus, Sleep, MoodEntry, PhysicalActivity, Meal, HabitDefinition, HabitLog
from django.db.models import Avg, Sum
import random
from main.models import Notification, HealthStatus, Sleep, MoodEntry, PhysicalActivity, Meal, HabitDefinition, HabitLog
from django.db.models import Avg, Sum
import random
from django.utils import timezone
from datetime import timedelta
class NotificationService:
    """خدمة إنشاء الإشعارات التلقائية - نسخة متكاملة"""
    
    @staticmethod
    def check_health_alerts(user):
        """فحص التنبيهات الصحية"""
        latest = HealthStatus.objects.filter(user=user).order_by('-recorded_at').first()
        if not latest:
            return []
        
        notifications = []
        
        # 1. فحص الوزن (مرتفع ومنخفض)
        if latest.weight_kg:
            weight = float(latest.weight_kg)
            if weight > 100:
                notifications.append({
                    'type': 'health',
                    'priority': 'high',
                    'icon': '⚖️',
                    'title': '⚠️ تنبيه الوزن',
                    'message': f'وزنك {weight} كجم أعلى من المعدل',
                    'suggestions': ['استشر أخصائي تغذية', 'زد نشاطك البدني', 'قلل السكريات']
                })
            elif weight < 50:
                notifications.append({
                    'type': 'health',
                    'priority': 'high',
                    'icon': '⚖️',
                    'title': '⚠️ نقص الوزن',
                    'message': f'وزنك {weight} كجم أقل من المعدل',
                    'suggestions': ['تحتاج تغذية غنية بالسعرات', 'استشر أخصائي تغذية']
                })
        
        # 2. فحص الضغط (مرتفع ومنخفض)
        if latest.systolic_pressure and latest.diastolic_pressure:
            systolic = latest.systolic_pressure
            diastolic = latest.diastolic_pressure
            
            if systolic > 140 or diastolic > 90:
                notifications.append({
                    'type': 'health',
                    'priority': 'high',
                    'icon': '❤️',
                    'title': '❤️ ضغط مرتفع',
                    'message': f'ضغطك {systolic}/{diastolic}',
                    'suggestions': ['قلل الملح', 'مارس المشي', 'استشر طبيباً']
                })
            elif systolic < 90 or diastolic < 60:
                notifications.append({
                    'type': 'health',
                    'priority': 'medium',
                    'icon': '❤️',
                    'title': '❤️ ضغط منخفض',
                    'message': f'ضغطك {systolic}/{diastolic}',
                    'suggestions': ['اشرب ماء', 'تناول وجبة خفيفة', 'استشر طبيباً']
                })
        
        # 3. فحص السكر (مرتفع ومنخفض)
        if latest.blood_glucose:
            glucose = float(latest.blood_glucose)
            if glucose > 140:
                notifications.append({
                    'type': 'health',
                    'priority': 'high',
                    'icon': '🩸',
                    'title': '🩸 سكر مرتفع',
                    'message': f'نسبة السكر {glucose} mg/dL',
                    'suggestions': ['قلل الحلويات', 'تناول وجبات صغيرة', 'راقب سكرك']
                })
            elif glucose < 70:
                notifications.append({
                    'type': 'health',
                    'priority': 'urgent',
                    'icon': '🆘',
                    'title': '🆘 سكر منخفض',
                    'message': f'نسبة السكر {glucose} mg/dL',
                    'suggestions': ['تناول عصير', 'كل تمرة', 'لا تتأخر في الوجبات']
                })
        
        return notifications
    
    @staticmethod
    def check_sleep_alerts(user):
        """فحص تنبيهات النوم"""
        now = timezone.now()
        today = now.date()
        notifications = []
        
        # 1. تذكير بالنوم (بعد 9 مساءً)
        if now.hour >= 21:
            # تحقق مما إذا كان قد نام بالفعل
            slept_today = Sleep.objects.filter(
                user=user,
                sleep_start__date=today
            ).exists()
            
            if not slept_today:
                notifications.append({
                    'type': 'sleep',
                    'priority': 'medium',
                    'icon': '🌙',
                    'title': '🌙 وقت النوم',
                    'message': 'حاول النوم قبل 11 مساءً لنوم صحي',
                    'suggestions': ['أطفئ الأضواء', 'ابتعد عن الشاشات', 'اشرب شاي أعشاب']
                })
        
        # 2. تحليل جودة النوم (صباحاً)
        if 8 <= now.hour <= 10:
            yesterday = today - timedelta(days=1)
            last_sleep = Sleep.objects.filter(
                user=user,
                sleep_start__date=yesterday
            ).first()
            
            if last_sleep and last_sleep.duration_hours:
                hours = float(last_sleep.duration_hours)
                if hours < 6:
                    notifications.append({
                        'type': 'sleep',
                        'priority': 'high',
                        'icon': '😴',
                        'title': '😴 قلة النوم',
                        'message': f'نمتَ {hours:.1f} ساعات فقط الليلة الماضية',
                        'suggestions': ['حاول النوم مبكراً الليلة', 'تجنب الكافيين بعد العصر']
                    })
                elif hours > 9:
                    notifications.append({
                        'type': 'sleep',
                        'priority': 'medium',
                        'icon': '😴',
                        'title': '😴 نوم طويل',
                        'message': f'نمتَ {hours:.1f} ساعات (أكثر من المعدل)',
                        'suggestions': ['النوم الطويل قد يسبب الخمول', 'حاول تنظيم نومك']
                    })
        
        return notifications
    
    @staticmethod
    def check_habit_alerts(user):
        """فحص تنبيهات العادات"""
        today = timezone.now().date()
        now = timezone.now()
        notifications = []
        
        habits = HabitDefinition.objects.filter(user=user)
        
        for habit in habits:
            logged_today = HabitLog.objects.filter(
                habit=habit,
                log_date=today
            ).exists()
            
            # تذكير في المساء فقط (بعد 6 مساءً)
            if not logged_today and now.hour >= 18:
                notifications.append({
                    'type': 'habit',
                    'priority': 'low',
                    'icon': '💊',
                    'title': f'💊 {habit.name}',
                    'message': 'لم تسجل هذه العادة اليوم',
                    'action_url': f'/habits/{habit.id}',
                    'action_text': 'سجل الآن'
                })
        
        return notifications
    
    @staticmethod
    def check_nutrition_alerts(user):
        """فحص تنبيهات التغذية"""
        now = timezone.now()
        today = now.date()
        notifications = []
        
        # 1. تذكير بالإفطار (7-9 صباحاً)
        if 7 <= now.hour <= 9:
            breakfast_today = Meal.objects.filter(
                user=user,
                meal_type='Breakfast',
                meal_time__date=today
            ).exists()
            
            if not breakfast_today:
                notifications.append({
                    'type': 'nutrition',
                    'priority': 'medium',
                    'icon': '🥗',
                    'title': '🌅 وجبة الإفطار',
                    'message': 'لا تنسى وجبة الإفطار لتبدأ يومك بنشاط',
                    'suggestions': [
                        '🥚 بيض + خبز أسمر',
                        '🥣 شوفان مع فواكه',
                        '🥑 توست مع أفوكادو'
                    ]
                })
        
        # 2. تذكير بالغداء (12-2 ظهراً)
        if 12 <= now.hour <= 14:
            lunch_today = Meal.objects.filter(
                user=user,
                meal_type='Lunch',
                meal_time__date=today
            ).exists()
            
            if not lunch_today:
                notifications.append({
                    'type': 'nutrition',
                    'priority': 'medium',
                    'icon': '🍲',
                    'title': '☀️ وجبة الغداء',
                    'message': 'حان وقت الغداء',
                    'suggestions': ['🍗 بروتين', '🥗 سلطة', '🍚 كربوهيدرات']
                })
        
        # 3. تذكير بالعشاء (6-8 مساءً)
        if 18 <= now.hour <= 20:
            dinner_today = Meal.objects.filter(
                user=user,
                meal_type='Dinner',
                meal_time__date=today
            ).exists()
            
            if not dinner_today:
                notifications.append({
                    'type': 'nutrition',
                    'priority': 'low',
                    'icon': '🥗',
                    'title': '🌙 وجبة العشاء',
                    'message': 'وجبة خفيفة قبل النوم',
                    'suggestions': ['🥛 زبادي', '🍎 فاكهة', '🌿 شاي أعشاب']
                })
        
        return notifications
    
    @staticmethod
    def check_activity_alerts(user):
        """فحص تنبيهات النشاط البدني"""
        now = timezone.now()
        today = now.date()
        notifications = []
        
        # تذكير بالمشي (4-6 مساءً)
        if 16 <= now.hour <= 18:
            activity_today = PhysicalActivity.objects.filter(
                user=user,
                start_time__date=today
            ).exists()
            
            if not activity_today:
                notifications.append({
                    'type': 'activity',
                    'priority': 'medium',
                    'icon': '🚶',
                    'title': '🚶 وقت المشي',
                    'message': 'لم تمارس أي نشاط اليوم',
                    'suggestions': ['🚶 امشِ 30 دقيقة', '🧘 تمارين تمدد', '🏃 10 دقائق فقط']
                })
        
        return notifications
    
    @staticmethod
    def check_achievements(user):
        """فحص إنجازات المستخدم"""
        notifications = []
        
        # إنجاز عدد القراءات الصحية
        health_count = HealthStatus.objects.filter(user=user).count()
        if health_count > 0 and health_count % 10 == 0:
            notifications.append({
                'type': 'achievement',
                'priority': 'low',
                'icon': '🏆',
                'title': '🏆 إنجاز جديد',
                'message': f'لقد سجلت {health_count} قراءة صحية',
                'suggestions': ['استمر في تتبع صحتك']
            })
        
        # إنجاز النوم
        sleep_count = Sleep.objects.filter(user=user).count()
        if sleep_count > 0 and sleep_count % 7 == 0:
            weeks = sleep_count // 7
            notifications.append({
                'type': 'achievement',
                'priority': 'low',
                'icon': '🌙',
                'title': '🌙 خبير النوم',
                'message': f'أكملت {weeks} أسابيع من تتبع النوم'
            })
        
        return notifications
    
    @staticmethod
    def get_daily_tip():
        """نصيحة يومية عشوائية"""
        tips = [
            {
                'type': 'tip',
                'priority': 'low',
                'icon': '💡',
                'title': '💡 نصيحة صحية',
                'message': 'شرب الماء قبل الوجبات يساعد على الشعور بالشبع'
            },
            {
                'type': 'tip',
                'priority': 'low',
                'icon': '💡',
                'title': '💡 نصيحة للنوم',
                'message': 'تجنب الشاشات قبل النوم بساعة لتحسين جودة النوم'
            },
            {
                'type': 'tip',
                'priority': 'low',
                'icon': '💡',
                'title': '💡 نصيحة للطاقة',
                'message': 'المشي 10 دقائق بعد الأكل يساعد على الهضم'
            },
            {
                'type': 'motivation',
                'priority': 'low',
                'icon': '🌟',
                'title': '🌟 هل تعلم؟',
                'message': 'الضحك يحرق سعرات حرارية ويحسن المزاج!'
            }
        ]
        return random.choice(tips)
    
    @staticmethod
    def generate_all_notifications(user):
        """توليد كل الإشعارات للمستخدم"""
        all_notifications = []
        today = timezone.now().date()
        
        # تجميع كل الإشعارات
        all_notifications.extend(NotificationService.check_health_alerts(user))
        all_notifications.extend(NotificationService.check_sleep_alerts(user))
        all_notifications.extend(NotificationService.check_habit_alerts(user))
        all_notifications.extend(NotificationService.check_nutrition_alerts(user))
        all_notifications.extend(NotificationService.check_activity_alerts(user))
        all_notifications.extend(NotificationService.check_achievements(user))
        
        # إضافة نصيحة يومية (مرة واحدة فقط)
        tip_exists = Notification.objects.filter(
            user=user,
            type='tip',
            sent_at__date=today
        ).exists()
        
        if not tip_exists and random.random() < 0.3:  # 30% فرصة
            all_notifications.append(NotificationService.get_daily_tip())
        
        # حفظ الإشعارات (تجنب التكرار)
        created_count = 0
        for notif_data in all_notifications:
            # تحقق من عدم وجود إشعار مكرر اليوم
            exists = Notification.objects.filter(
                user=user,
                type=notif_data['type'],
                title=notif_data['title'],
                sent_at__date=today
            ).exists()
            
            if not exists:
                Notification.objects.create(
                    user=user,
                    sent_at=timezone.now(),
                    **notif_data
                )
                created_count += 1
        
        if created_count > 0:
            print(f"✅ تم إنشاء {created_count} إشعار لـ {user.username}")
        
        return created_count