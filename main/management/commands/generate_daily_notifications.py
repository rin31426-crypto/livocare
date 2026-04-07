# main/management/commands/generate_daily_notifications.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import Notification, HabitDefinition, HabitLog
from main.services.notification_service import NotificationService
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'توليد الإشعارات اليومية لجميع المستخدمين'
    
    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)
        today = timezone.now().date()
        notification_count = 0
        
        for user in users:
            user_notifications = 0
            self.stdout.write(f"\n🔔 جاري معالجة المستخدم: {user.username}")
            
            # ✅ استخدام خدمة الإشعارات الموجودة (تعيد عدد الإشعارات)
            service_count = NotificationService.generate_all_notifications(user)
            if service_count:
                user_notifications += service_count
                self.stdout.write(f"   ✅ من الخدمة: {service_count} إشعار")
            
            # ✅ إضافة تذكيرات بالعادات اليومية
            habits = HabitDefinition.objects.filter(user=user, is_active=True)
            for habit in habits:
                logged_today = HabitLog.objects.filter(
                    habit=habit,
                    log_date=today
                ).exists()
                
                if not logged_today:
                    # تحقق من عدم وجود إشعار مكرر اليوم
                    existing = Notification.objects.filter(
                        user=user,
                        type='habit',
                        title__icontains=habit.name,
                        sent_at__date=today
                    ).exists()
                    
                    if not existing:
                        Notification.objects.create(
                            user=user,
                            type='habit',
                            priority='low',
                            icon='💊',
                            title=f'💊 {habit.name}',
                            message='لم تسجل هذه العادة اليوم',
                            sent_at=timezone.now()
                        )
                        user_notifications += 1
                        self.stdout.write(f"   ✅ إشعار عادة: {habit.name}")
            
            # ✅ إضافة تذكير المساء (إذا كان الوقت مناسباً)
            current_hour = timezone.now().hour
            if 18 <= current_hour <= 20:  # بين 6 و 8 مساءً
                evening_reminder_exists = Notification.objects.filter(
                    user=user,
                    type='reminder',
                    title__icontains='المساء',
                    sent_at__date=today
                ).exists()
                
                if not evening_reminder_exists:
                    Notification.objects.create(
                        user=user,
                        type='reminder',
                        priority='medium',
                        icon='🌙',
                        title='🌙 تذكير المساء',
                        message='كيف كان يومك؟ لا تنسى تسجيل نشاطك ومزاجك اليوم',
                        action_url='/mood',
                        action_text='سجل الآن',
                        sent_at=timezone.now()
                    )
                    user_notifications += 1
                    self.stdout.write(f"   ✅ إشعار مسائي")
            
            if user_notifications > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ تم إنشاء {user_notifications} إشعار لـ {user.username}')
                )
                notification_count += user_notifications
            else:
                self.stdout.write(f'   ℹ️ لا توجد إشعارات جديدة لـ {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 الإجمالي: {notification_count} إشعار لـ {users.count()} مستخدم')
        )