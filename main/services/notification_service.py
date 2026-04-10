# main/services/notification_service.py
import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count, Avg, Sum
from django.contrib.auth import get_user_model
import random
import requests
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
User = get_user_model()

# ✅ روابط الخدمات الخارجية
NOTIFICATION_SERVICE_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'https://notification-service-2xej.onrender.com')
EMAIL_SERVICE_URL = os.environ.get('EMAIL_SERVICE_URL', 'https://email-service-zc0r.onrender.com')

# ✅ نطاق التطبيق للروابط
APP_URL = os.environ.get('APP_URL', 'https://livocare-fronend.onrender.com')


class NotificationService:
    """خدمة إنشاء وإرسال الإشعارات التلقائية"""

    @staticmethod
    def send_push_notification(user, title: str, message: str, icon: str = None, url: str = '/', priority: str = 'normal'):
        """
        إرسال إشعار فوري عبر الخدمة المستقلة
        """
        if not user or not user.is_active:
            return False
        
        try:
            payload = {
                'user_id': user.id,
                'title': title,
                'body': message,
                'icon': icon or '/logo192.png',
                'url': url,
                'priority': priority
            }
            
            response = requests.post(
                f'{NOTIFICATION_SERVICE_URL}/api/notify/',
                json=payload,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"📱 Push sent to {user.username}: {title}")
                return True
            else:
                logger.warning(f"❌ Push failed for {user.username}: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Push timeout for {user.username}")
            return False
        except Exception as e:
            logger.error(f"❌ Push error for {user.username}: {e}")
            return False

    @staticmethod
    def send_email_notification(user, title: str, message: str):
        """
        إرسال إشعار عبر خدمة البريد المستقلة
        """
        if not user or not user.email:
            logger.warning(f"❌ No email for {user.username if user else 'Unknown'}")
            return False
        
        try:
            payload = {
                'to': user.email,
                'subject': f'🔔 LivoCare: {title}',
                'message': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">🔔 {title}</h2>
                    <p style="font-size: 16px; line-height: 1.5;">{message}</p>
                    <hr style="margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        هذا إشعار تلقائي من تطبيق LivoCare.<br>
                        <a href="{APP_URL}" style="color: #4F46E5;">زيارة التطبيق</a>
                    </p>
                </div>
                """,
                'html': True
            }
            
            response = requests.post(
                f'{EMAIL_SERVICE_URL}/api/send/',
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"📧 Email sent to {user.email}: {title}")
                return True
            else:
                logger.warning(f"❌ Email failed for {user.email}: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ Email timeout for {user.email}")
            return False
        except Exception as e:
            logger.error(f"❌ Email error for {user.email}: {e}")
            return False

    @staticmethod
    def save_notification(user, notif_data: Dict[str, Any]) -> bool:
        """
        حفظ الإشعار في قاعدة البيانات
        """
        from main.models import Notification
        
        try:
            # التحقق من عدم وجود إشعار مكرر خلال الـ 6 ساعات الماضية
            six_hours_ago = timezone.now() - timedelta(hours=6)
            exists = Notification.objects.filter(
                user=user,
                type=notif_data.get('type', 'alert'),
                title=notif_data.get('title', ''),
                sent_at__gte=six_hours_ago
            ).exists()
            
            if exists:
                logger.debug(f"Duplicate notification skipped: {notif_data.get('title')}")
                return False
            
            Notification.objects.create(
                user=user,
                sent_at=timezone.now(),
                is_read=False,
                is_archived=False,
                **notif_data
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save notification: {e}")
            return False

    # =========================================================
    # 1. التنبيهات الصحية
    # =========================================================
    
    @staticmethod
    def check_health_alerts(user) -> List[Dict[str, Any]]:
        """فحص التنبيهات الصحية"""
        from main.models import HealthStatus
        
        notifications = []
        latest = HealthStatus.objects.filter(user=user).order_by('-recorded_at').first()
        
        if not latest:
            return notifications
        
        # 1. فحص الوزن
        if latest.weight_kg:
            weight = float(latest.weight_kg)
            
            if weight > 100:
                notif = {
                    'type': 'health',
                    'priority': 'high',
                    'severity': 'warning',
                    'icon': '⚖️',
                    'title': '⚠️ ارتفاع الوزن',
                    'message': f'وزنك {weight:.1f} كجم أعلى من المعدل الطبيعي',
                    'suggestions': [
                        'استشر أخصائي تغذية',
                        'زد نشاطك البدني',
                        'قلل السكريات والدهون'
                    ],
                    'action_url': '/health',
                    'action_text': 'عرض القراءات',
                    'value': weight
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health')
                
            elif weight < 50:
                notif = {
                    'type': 'health',
                    'priority': 'high',
                    'severity': 'warning',
                    'icon': '⚖️',
                    'title': '⚠️ نقص الوزن',
                    'message': f'وزنك {weight:.1f} كجم أقل من المعدل الطبيعي',
                    'suggestions': [
                        'تحتاج تغذية غنية بالسعرات',
                        'استشر أخصائي تغذية',
                        'أضف وجبات خفيفة صحية'
                    ],
                    'action_url': '/health',
                    'action_text': 'عرض القراءات',
                    'value': weight
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health')
        
        # 2. فحص ضغط الدم
        if latest.systolic_pressure and latest.diastolic_pressure:
            systolic = latest.systolic_pressure
            diastolic = latest.diastolic_pressure
            
            if systolic > 140 or diastolic > 90:
                notif = {
                    'type': 'health',
                    'priority': 'urgent',
                    'severity': 'danger',
                    'icon': '❤️',
                    'title': '⚠️ ضغط الدم مرتفع',
                    'message': f'ضغطك {systolic}/{diastolic} mmHg',
                    'suggestions': [
                        'قلل الملح في الطعام',
                        'مارس المشي يومياً',
                        'استشر طبيباً للمتابعة'
                    ],
                    'action_url': '/health',
                    'action_text': 'عرض التفاصيل',
                    'value': systolic
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health', priority='high')
                NotificationService.send_email_notification(user, notif['title'], notif['message'])
                
            elif systolic < 90 or diastolic < 60:
                notif = {
                    'type': 'health',
                    'priority': 'high',
                    'severity': 'warning',
                    'icon': '❤️',
                    'title': '⚠️ ضغط الدم منخفض',
                    'message': f'ضغطك {systolic}/{diastolic} mmHg',
                    'suggestions': [
                        'اشرب كمية كافية من الماء',
                        'تناول وجبات صغيرة متكررة',
                        'استشر طبيباً إذا استمر الانخفاض'
                    ],
                    'action_url': '/health',
                    'action_text': 'عرض التفاصيل',
                    'value': systolic
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health')
        
        # 3. فحص السكر
        if latest.glucose_mgdl:
            glucose = float(latest.glucose_mgdl)
            
            if glucose > 140:
                notif = {
                    'type': 'health',
                    'priority': 'high',
                    'severity': 'warning',
                    'icon': '🩸',
                    'title': '⚠️ ارتفاع السكر',
                    'message': f'نسبة السكر {glucose:.1f} mg/dL',
                    'suggestions': [
                        'قلل الحلويات والمشروبات السكرية',
                        'تناول وجبات صغيرة متعددة',
                        'مارس الرياضة بانتظام'
                    ],
                    'action_url': '/health',
                    'action_text': 'عرض القراءات',
                    'value': glucose
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health')
                NotificationService.send_email_notification(user, notif['title'], notif['message'])
                
            elif glucose < 70:
                notif = {
                    'type': 'health',
                    'priority': 'urgent',
                    'severity': 'danger',
                    'icon': '🆘',
                    'title': '🚨 انخفاض السكر',
                    'message': f'نسبة السكر {glucose:.1f} mg/dL',
                    'suggestions': [
                        'تناول عصير فواكه طبيعي',
                        'كل تمرة أو قطعة حلوى صغيرة',
                        'لا تتأخر في وجباتك'
                    ],
                    'action_url': '/health',
                    'action_text': 'تسجيل قراءة جديدة',
                    'value': glucose
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health', priority='high')
                NotificationService.send_email_notification(user, notif['title'], notif['message'])
        
        return notifications

    # =========================================================
    # 2. تنبيهات النوم
    # =========================================================
    
    @staticmethod
    def check_sleep_alerts(user) -> List[Dict[str, Any]]:
        """فحص تنبيهات النوم"""
        from main.models import Sleep
        
        now = timezone.now()
        today = now.date()
        notifications = []
        
        # 1. تذكير بالنوم (بعد 9 مساءً)
        if 21 <= now.hour <= 23:
            slept_today = Sleep.objects.filter(
                user=user,
                sleep_start__date=today
            ).exists()
            
            if not slept_today:
                notif = {
                    'type': 'sleep',
                    'priority': 'medium',
                    'severity': 'info',
                    'icon': '🌙',
                    'title': '🌙 وقت النوم',
                    'message': 'حان وقت الاستعداد للنوم',
                    'suggestions': [
                        'أطفئ الأضواء الزرقاء من الشاشات',
                        'اشرب كوباً من الشاي العشبي',
                        'اجعل غرفتك مظلمة وباردة'
                    ],
                    'action_url': '/sleep',
                    'action_text': 'تسجيل النوم'
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/sleep')
        
        # 2. تحليل النوم (صباحاً)
        elif 7 <= now.hour <= 10:
            yesterday = today - timedelta(days=1)
            last_sleep = Sleep.objects.filter(
                user=user,
                sleep_start__date=yesterday
            ).first()
            
            if last_sleep:
                # حساب المدة بالساعات
                if last_sleep.sleep_start and last_sleep.sleep_end:
                    duration = (last_sleep.sleep_end - last_sleep.sleep_start).total_seconds() / 3600
                    
                    if duration < 6:
                        notif = {
                            'type': 'sleep',
                            'priority': 'high',
                            'severity': 'warning',
                            'icon': '😴',
                            'title': '😴 قلة النوم',
                            'message': f'نمتَ {duration:.1f} ساعات فقط الليلة الماضية',
                            'suggestions': [
                                'حاول النوم مبكراً الليلة',
                                'تجنب الكافيين بعد الساعة 4 مساءً',
                                'مارس نشاطاً مريحاً قبل النوم'
                            ],
                            'action_url': '/sleep',
                            'action_text': 'تحليل النوم',
                            'value': duration
                        }
                        notifications.append(notif)
                        NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/sleep')
                        NotificationService.send_email_notification(user, notif['title'], notif['message'])
                        
                    elif duration > 9:
                        notif = {
                            'type': 'sleep',
                            'priority': 'medium',
                            'severity': 'info',
                            'icon': '😴',
                            'title': '😴 نوم طويل',
                            'message': f'نمتَ {duration:.1f} ساعات',
                            'suggestions': [
                                'النوم الطويل قد يسبب الخمول',
                                'حاول تنظيم مواعيد نومك',
                                'استيقظ في وقت ثابت يومياً'
                            ],
                            'action_url': '/sleep',
                            'action_text': 'تحليل النوم',
                            'value': duration
                        }
                        notifications.append(notif)
                        NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/sleep')
        
        return notifications

    # =========================================================
    # 3. تنبيهات العادات
    # =========================================================
    
    @staticmethod
    def check_habit_alerts(user) -> List[Dict[str, Any]]:
        """فحص تنبيهات العادات"""
        from main.models import HabitDefinition, HabitLog
        
        today = timezone.now().date()
        now = timezone.now()
        notifications = []
        
        habits = HabitDefinition.objects.filter(user=user, is_active=True)
        
        for habit in habits:
            logged_today = HabitLog.objects.filter(
                habit=habit,
                log_date=today
            ).exists()
            
            # تذكير بعد الساعة 6 مساءً للعادات التي لم تسجل
            if not logged_today and now.hour >= 18:
                notif = {
                    'type': 'habit',
                    'priority': 'low',
                    'severity': 'info',
                    'icon': '💊',
                    'title': f'💊 تذكير: {habit.name}',
                    'message': 'لم تسجل هذه العادة اليوم',
                    'suggestions': [
                        'خذ دقيقة لتسجيل عادتك',
                        'حافظ على اتساق عاداتك اليومية'
                    ],
                    'action_url': f'/habits/{habit.id}',
                    'action_text': 'سجل الآن'
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url=notif['action_url'])
        
        return notifications

    # =========================================================
    # 4. تنبيهات التغذية
    # =========================================================
    
    @staticmethod
    def check_nutrition_alerts(user) -> List[Dict[str, Any]]:
        """فحص تنبيهات التغذية"""
        from main.models import Meal
        
        now = timezone.now()
        today = now.date()
        notifications = []
        
        # تعريف أوقات الوجبات
        meal_times = {
            'Breakfast': {'start': 7, 'end': 9, 'icon': '🌅', 'title': 'وجبة الإفطار', 'message': 'لا تنسى وجبة الإفطار لبدء يومك بنشاط'},
            'Lunch': {'start': 12, 'end': 14, 'icon': '☀️', 'title': 'وجبة الغداء', 'message': 'حان وقت الغداء'},
            'Dinner': {'start': 18, 'end': 20, 'icon': '🌙', 'title': 'وجبة العشاء', 'message': 'وجبة خفيفة قبل النوم'}
        }
        
        for meal_type, info in meal_times.items():
            if info['start'] <= now.hour <= info['end']:
                meal_exists = Meal.objects.filter(
                    user=user,
                    meal_type=meal_type,
                    meal_time__date=today
                ).exists()
                
                if not meal_exists:
                    suggestions = {
                        'Breakfast': ['🥚 بيض مع خبز أسمر', '🥣 شوفان مع فواكه', '🥑 توست مع أفوكادو'],
                        'Lunch': ['🍗 بروتين (دجاج/سمك)', '🥗 سلطة خضراء', '🍚 كربوهيدرات صحية'],
                        'Dinner': ['🥛 زبادي مع فواكه', '🍎 تفاح أو موز', '🌿 شاي أعشاب مهدئ']
                    }
                    
                    notif = {
                        'type': 'nutrition',
                        'priority': 'medium' if meal_type != 'Dinner' else 'low',
                        'severity': 'info',
                        'icon': info['icon'],
                        'title': f'{info["icon"]} {info["title"]}',
                        'message': info['message'],
                        'suggestions': suggestions.get(meal_type, ['حافظ على نظام غذائي متوازن']),
                        'action_url': '/nutrition',
                        'action_text': 'تسجيل وجبة'
                    }
                    notifications.append(notif)
                    NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/nutrition')
        
        return notifications

    # =========================================================
    # 5. تنبيهات النشاط البدني
    # =========================================================
    
    @staticmethod
    def check_activity_alerts(user) -> List[Dict[str, Any]]:
        """فحص تنبيهات النشاط البدني"""
        from main.models import PhysicalActivity
        
        now = timezone.now()
        today = now.date()
        notifications = []
        
        # وقت تذكير النشاط (4-6 مساءً)
        if 16 <= now.hour <= 18:
            activity_today = PhysicalActivity.objects.filter(
                user=user,
                start_time__date=today
            ).exists()
            
            if not activity_today:
                notif = {
                    'type': 'activity',
                    'priority': 'medium',
                    'severity': 'info',
                    'icon': '🚶',
                    'title': '🚶 وقت النشاط',
                    'message': 'لم تمارس أي نشاط بدني اليوم',
                    'suggestions': [
                        '🚶 امشِ 20-30 دقيقة',
                        '🧘 تمارين تمدد خفيفة',
                        '🏃 جرب تمريناً سريعاً لمدة 10 دقائق'
                    ],
                    'action_url': '/activities',
                    'action_text': 'تسجيل نشاط'
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/activities')
        
        return notifications

    # =========================================================
    # 6. إنجازات المستخدم
    # =========================================================
    
    @staticmethod
    def check_achievements(user) -> List[Dict[str, Any]]:
        """فحص إنجازات المستخدم"""
        from main.models import HealthStatus, Sleep
        
        notifications = []
        
        # إنجازات القراءات الصحية
        health_count = HealthStatus.objects.filter(user=user).count()
        achievement_milestones = [10, 25, 50, 100]
        
        for milestone in achievement_milestones:
            if health_count == milestone:
                notif = {
                    'type': 'achievement',
                    'priority': 'low',
                    'severity': 'success',
                    'icon': '🏆',
                    'title': f'🏆 {milestone} قراءة صحية!',
                    'message': f'مبروك! لقد سجلت {milestone} قراءة صحية',
                    'suggestions': ['استمر في تتبع صحتك', 'شارك إنجازك مع الأصدقاء'],
                    'action_url': '/health',
                    'action_text': 'عرض القراءات'
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/health')
                NotificationService.send_email_notification(user, notif['title'], notif['message'])
                break
        
        # إنجازات النوم
        sleep_count = Sleep.objects.filter(user=user).count()
        sleep_milestones = [7, 30, 100]
        
        for milestone in sleep_milestones:
            if sleep_count == milestone:
                weeks = milestone // 7
                notif = {
                    'type': 'achievement',
                    'priority': 'low',
                    'severity': 'success',
                    'icon': '🌙',
                    'title': f'🌙 {weeks} أسابيع من تتبع النوم',
                    'message': f'أكملت {milestone} ليلة من تتبع نومك',
                    'suggestions': ['حافظ على جودة نومك', 'راقب تحسن نومك'],
                    'action_url': '/sleep',
                    'action_text': 'تحليل النوم'
                }
                notifications.append(notif)
                NotificationService.send_push_notification(user, notif['title'], notif['message'], icon=notif['icon'], url='/sleep')
                break
        
        return notifications

    # =========================================================
    # 7. النصائح اليومية
    # =========================================================
    
    @staticmethod
    def get_daily_tip() -> Dict[str, Any]:
        """نصيحة يومية عشوائية"""
        tips = [
            {'type': 'tip', 'icon': '💧', 'title': '💧 شرب الماء', 'message': 'اشرب كوباً من الماء قبل كل وجبة للمساعدة على الهضم'},
            {'type': 'tip', 'icon': '😴', 'title': '😴 النوم الجيد', 'message': 'تجنب الشاشات قبل النوم بساعة لتحسين جودة النوم'},
            {'type': 'tip', 'icon': '🚶', 'title': '🚶 الحركة', 'message': 'المشي 10 دقائق بعد الأكل يساعد على الهضم ويحسن المزاج'},
            {'type': 'tip', 'icon': '🥗', 'title': '🥗 التغذية', 'message': 'أضف لوناً جديداً من الخضروات إلى وجبتك اليوم'},
            {'type': 'tip', 'icon': '🧘', 'title': '🧘 التأمل', 'message': 'خذ 5 دقائق للتأمل والتنفس العميق لتقليل التوتر'},
            {'type': 'tip', 'icon': '📝', 'title': '📝 اليوميات', 'message': 'دوّن 3 أشياء تشعر بالامتنان لها اليوم'},
            {'type': 'tip', 'icon': '🏃', 'title': '🏃 النشاط', 'message': 'حاول صعود الدرج بدلاً من المصعد لزيادة نشاطك'},
            {'type': 'tip', 'icon': '🍎', 'title': '🍎 الفواكه', 'message': 'تناول فاكهة طازجة بدلاً من العصائر المعلبة'},
            {'type': 'motivation', 'icon': '🌟', 'title': '🌟 تحفيز', 'message': 'الاستمرارية أهم من الكمال. استمر في رحلتك الصحية!'},
        ]
        return random.choice(tips)

    # =========================================================
    # 8. الوظيفة الرئيسية - توليد جميع الإشعارات
    # =========================================================
    
    @staticmethod
    def generate_all_notifications(user) -> int:
        """
        توليد وإرسال جميع الإشعارات للمستخدم
        إرجاع عدد الإشعارات التي تم إنشاؤها
        """
        if not user or not user.is_active:
            logger.warning(f"User {user} is not active, skipping notifications")
            return 0
        
        all_notifications = []
        today = timezone.now().date()
        
        logger.info(f"🔔 Generating notifications for {user.username}")
        
        # جمع جميع الإشعارات
        all_notifications.extend(NotificationService.check_health_alerts(user))
        all_notifications.extend(NotificationService.check_sleep_alerts(user))
        all_notifications.extend(NotificationService.check_habit_alerts(user))
        all_notifications.extend(NotificationService.check_nutrition_alerts(user))
        all_notifications.extend(NotificationService.check_activity_alerts(user))
        all_notifications.extend(NotificationService.check_achievements(user))
        
        # نصيحة يومية (مرة واحدة في اليوم)
        tip_exists = NotificationService.notification_exists_today(user, 'tip')
        if not tip_exists and random.random() < 0.3:  # 30% فرصة للحصول على نصيحة
            tip = NotificationService.get_daily_tip()
            all_notifications.append(tip)
            NotificationService.send_push_notification(user, tip['title'], tip['message'], icon=tip['icon'], url='/')
        
        # حفظ الإشعارات في قاعدة البيانات
        created_count = 0
        for notif_data in all_notifications:
            if NotificationService.save_notification(user, notif_data):
                created_count += 1
        
        if created_count > 0:
            logger.info(f"✅ Created {created_count} notifications for {user.username}")
        else:
            logger.debug(f"No new notifications for {user.username}")
        
        return created_count
    
    @staticmethod
    def notification_exists_today(user, notif_type: str) -> bool:
        """التحقق من وجود إشعار من نوع معين اليوم"""
        from main.models import Notification
        
        today = timezone.now().date()
        return Notification.objects.filter(
            user=user,
            type=notif_type,
            sent_at__date=today
        ).exists()