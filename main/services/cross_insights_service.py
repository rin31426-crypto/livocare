"""
محرك الذكاء الاصطناعي للتحليلات الصحية المتقاطعة
Cross-Data Analysis Engine for Health Insights
"""
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Avg, Sum, Count, Q, F
from django.db.models.functions import TruncDate
from main.models import (
    HealthStatus, PhysicalActivity, Sleep, 
    MoodEntry, Meal, HabitLog
)

class HealthInsightsEngine:
    """
    محرك متقدم لتحليل البيانات الصحية وإيجاد العلاقات الخفية
    Advanced engine for analyzing health data and finding hidden correlations
    """
    
    def __init__(self, user, language='ar'):
        self.user = user
        self.language = language  # 'ar' for Arabic, 'en' for English
        self.today = timezone.now().date()
        self.week_ago = self.today - timedelta(days=7)
        self.month_ago = self.today - timedelta(days=30)
    
    def _t(self, ar_text, en_text, **kwargs):
        """
        ترجمة النصوص حسب اللغة المحددة
        Translate texts based on selected language
        """
        text = ar_text if self.language == 'ar' else en_text
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                # إذا فشل التنسيق، نعيد النص بدون تغيير
                return text
        return text
    
    def analyze_all(self):
        """تحليل جميع الجوانب الصحية وإرجاع توصيات ذكية"""
        return {
            'vital_signs_analysis': self.analyze_vital_signs(),
            'activity_nutrition_correlation': self.analyze_activity_nutrition(),
            'sleep_mood_correlation': self.analyze_sleep_mood(),
            'weight_trend_analysis': self.analyze_weight_trends(),
            'blood_pressure_insights': self.analyze_blood_pressure(),
            'glucose_risk_assessment': self.analyze_glucose_risks(),
            'energy_consumption_alert': self.analyze_energy_consumption(),
            'pulse_pressure_analysis': self.analyze_pulse_pressure(),
            'pre_exercise_recommendation': self.analyze_pre_exercise_risk(),
            'holistic_recommendations': self.generate_holistic_recommendations(),
            'predictive_alerts': self.generate_predictive_alerts(),
        }
    
    def analyze_vital_signs(self):
        """
        تحليل العلامات الحيوية الحالية (الوزن، الضغط، السكر)
        بناءً على آخر قراءة
        """
        latest = HealthStatus.objects.filter(
            user=self.user
        ).order_by('-recorded_at').first()
        
        if not latest:
            return {
                'status': 'no_data', 
                'message': self._t('لا توجد بيانات كافية', 'Insufficient data')
            }
        
        insights = []
        alerts = []
        
        # 1. تحليل الوزن (Body Weight Analysis)
        weight = latest.weight_kg
        if weight:
            weight = float(weight)
            if weight < 50:
                insights.append({
                    'type': 'weight',
                    'severity': 'warning',
                    'message': self._t('⚠️ وزنك منخفض جداً', '⚠️ Your weight is very low'),
                    'details': self._t(
                        f'{weight} كجم أقل من المعدل الطبيعي',
                        f'{weight} kg below normal range'
                    ),
                    'recommendation': self._t(
                        'تحتاج لزيادة السعرات الحرارية والبروتين',
                        'You need to increase calories and protein'
                    )
                })
                
                # ربط الوزن المنخفض بالنشاط البدني
                recent_activities = PhysicalActivity.objects.filter(
                    user=self.user,
                    start_time__date__gte=self.week_ago
                ).count()
                
                if recent_activities > 3:
                    alerts.append({
                        'type': 'weight_activity',
                        'message': self._t(
                            '⚡ وزنك منخفض مع نشاط عالي!',
                            '⚡ Low weight with high activity!'
                        ),
                        'details': self._t(
                            f'مع {recent_activities} تمارين هذا الأسبوع، قد تفقد كتلة عضلية',
                            f'With {recent_activities} exercises this week, you may lose muscle mass'
                        ),
                        'recommendation': self._t(
                            'زد كمية البروتين بعد التمرين مباشرة',
                            'Increase protein intake immediately after exercise'
                        )
                    })
            
            elif weight > 100:
                insights.append({
                    'type': 'weight',
                    'severity': 'warning',
                    'message': self._t('⚠️ وزنك مرتفع', '⚠️ Your weight is high'),
                    'details': self._t(
                        f'{weight} كجم أعلى من المعدل',
                        f'{weight} kg above normal range'
                    ),
                    'recommendation': self._t(
                        'جرب المشي 30 دقيقة يومياً وقلل السكريات',
                        'Try walking 30 minutes daily and reduce sugars'
                    )
                })
            else:
                insights.append({
                    'type': 'weight',
                    'severity': 'good',
                    'message': self._t('✅ وزنك في المعدل المثالي', '✅ Your weight is ideal'),
                    'details': self._t(f'{weight} كجم', f'{weight} kg'),
                    'recommendation': self._t(
                        'حافظ على نظامك الحالي',
                        'Maintain your current routine'
                    )
                })
        
        # 2. تحليل ضغط الدم (Blood Pressure Analysis)
        systolic = latest.systolic_pressure
        diastolic = latest.diastolic_pressure
        
        if systolic and diastolic:
            # تحليل فرق الضغط (Pulse Pressure)
            pulse_pressure = systolic - diastolic
            
            if pulse_pressure > 60:
                alerts.append({
                    'type': 'pulse_pressure',
                    'severity': 'high',
                    'message': self._t('❤️‍🩹 فرق الضغط كبير جداً', '❤️‍🩹 Pulse pressure is very high'),
                    'details': self._t(
                        f'الفرق {pulse_pressure} مم زئبق (الطبيعي 40-60)',
                        f'Difference {pulse_pressure} mmHg (normal 40-60)'
                    ),
                    'recommendation': self._t(
                        'قد يشير لصلابة الشرايين، استشر طبيباً',
                        'May indicate arterial stiffness, consult a doctor'
                    )
                })
            elif pulse_pressure < 30:
                alerts.append({
                    'type': 'pulse_pressure',
                    'severity': 'low',
                    'message': self._t('💓 فرق الضغط منخفض', '💓 Pulse pressure is low'),
                    'details': self._t(
                        f'الفرق {pulse_pressure} مم زئبق',
                        f'Difference {pulse_pressure} mmHg'
                    ),
                    'recommendation': self._t(
                        'قد يشير لضعف القلب، راقب الأعراض',
                        'May indicate heart weakness, monitor symptoms'
                    )
                })
            
            # حالة خاصة: ضغط انقباضي منخفض مع انبساطي مرتفع
            if systolic < 100 and diastolic > 85:
                alerts.append({
                    'type': 'bp_paradox',
                    'severity': 'critical',
                    'message': self._t('🫀 نمط ضغط غير طبيعي', '🫀 Abnormal blood pressure pattern'),
                    'details': self._t(
                        f'ضغط منخفض {systolic}/{diastolic}',
                        f'Low pressure {systolic}/{diastolic}'
                    ),
                    'recommendation': self._t(
                        'هذا النمط نادر ويحتاج استشارة طبية فورية',
                        'This rare pattern needs immediate medical consultation'
                    )
                })
        
        # 3. تحليل الجلوكوز (Glucose Analysis)
        glucose = latest.blood_glucose
        if glucose:
            glucose = float(glucose)
            if glucose > 140:
                insights.append({
                    'type': 'glucose',
                    'severity': 'high',
                    'message': self._t('🩸 سكر الدم مرتفع', '🩸 Blood sugar is high'),
                    'details': self._t(
                        f'{glucose} mg/dL أعلى من الطبيعي',
                        f'{glucose} mg/dL above normal'
                    ),
                    'recommendation': self._t(
                        'قلل الكربوهيدرات البسيطة وامش 15 دقيقة',
                        'Reduce simple carbs and walk 15 minutes'
                    )
                })
                
                # ربط السكر المرتفع بآخر وجبة
                last_meal = Meal.objects.filter(
                    user=self.user,
                    meal_time__date=self.today
                ).order_by('-meal_time').first()
                
                if last_meal:
                    high_carbs = any(
                        ing.get('carbs', 0) > 30 
                        for ing in last_meal.ingredients
                    )
                    if high_carbs:
                        alerts.append({
                            'type': 'meal_glucose',
                            'message': self._t(
                                '🍚 الوجبة الأخيرة غنية بالكربوهيدرات',
                                '🍚 Last meal was high in carbs'
                            ),
                            'details': self._t(
                                f'الوجبة: {last_meal.meal_type}',
                                f'Meal: {last_meal.meal_type}'
                            ),
                            'recommendation': self._t(
                                'اختر بروتيناً أكثر في الوجبة التالية',
                                'Choose more protein in your next meal'
                            )
                        })
            
            elif glucose < 70:
                insights.append({
                    'type': 'glucose',
                    'severity': 'low',
                    'message': self._t('🆘 سكر الدم منخفض!', '🆘 Blood sugar is low!'),
                    'details': self._t(
                        f'{glucose} mg/dL أقل من الطبيعي',
                        f'{glucose} mg/dL below normal'
                    ),
                    'recommendation': self._t(
                        'تناول مصدر سكر سريع (عصير، تمر)',
                        'Eat a quick sugar source (juice, dates)'
                    )
                })
        
        return {
            'vital_signs': {
                'weight': float(weight) if weight else None,
                'blood_pressure': f"{systolic}/{diastolic}" if systolic and diastolic else None,
                'glucose': float(glucose) if glucose else None,
                'recorded_at': latest.recorded_at
            },
            'insights': insights,
            'alerts': alerts,
            'pulse_pressure': pulse_pressure if systolic and diastolic else None
        }
    
    def analyze_energy_consumption(self):
        """
        تحليل استهلاك الطاقة وتقدير الاحتياج بناءً على الوزن والنشاط
        """
        latest = HealthStatus.objects.filter(
            user=self.user
        ).order_by('-recorded_at').first()
        
        if not latest or not latest.weight_kg:
            return {'status': 'insufficient_data'}
        
        weight = float(latest.weight_kg)
        
        # حساب معدل الأيض الأساسي (BMR) - تقريبي
        bmr = weight * 22  # معادلة مبسطة
        
        # حساب النشاط الأسبوعي
        weekly_activity = PhysicalActivity.objects.filter(
            user=self.user,
            start_time__date__gte=self.week_ago
        ).aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
        
        # متوسط النشاط اليومي
        daily_activity = weekly_activity / 7
        
        # إجمالي السعرات المحروقة يومياً
        total_daily_burn = bmr + daily_activity
        
        # متوسط السعرات المستهلكة
        avg_daily_intake = Meal.objects.filter(
            user=self.user,
            meal_time__date__gte=self.week_ago
        ).aggregate(Avg('total_calories'))['total_calories__avg'] or 0
        
        alerts = []
        recommendations = []
        
        # تحليل الوزن المنخفض مع النشاط العالي
        if weight < 55 and weekly_activity > 200:
            deficit = total_daily_burn - avg_daily_intake
            if deficit > 300:
                increase_percentage = min(30, int((deficit / avg_daily_intake) * 100)) if avg_daily_intake > 0 else 20
                
                alerts.append({
                    'type': 'energy_deficit',
                    'severity': 'critical',
                    'title': self._t('⚡ عجز في الطاقة', '⚡ Energy Deficit'),
                    'message': self._t(
                        f'وزنك {weight:.0f} كجم منخفض بالنسبة لنشاطك',
                        f'Your weight {weight:.0f} kg is low for your activity level'
                    ),
                    'details': self._t(
                        f'تحرق يومياً حوالي {int(total_daily_burn)} سعرة ولكن تستهلك فقط {int(avg_daily_intake)} سعرة',
                        f'You burn about {int(total_daily_burn)} calories daily but only consume {int(avg_daily_intake)} calories'
                    ),
                    'recommendation': self._t(
                        f'نوصي بزيادة سعراتك بنسبة {increase_percentage}%',
                        f'We recommend increasing your calories by {increase_percentage}%'
                    ),
                    'increase_percentage': increase_percentage
                })
                
                recommendations.append({
                    'icon': '🍌',
                    'title': self._t('زيادة السعرات', 'Increase Calories'),
                    'advice': self._t(
                        f'تحتاج {int(total_daily_burn - avg_daily_intake)} سعرة إضافية يومياً',
                        f'You need {int(total_daily_burn - avg_daily_intake)} extra calories daily'
                    ),
                    'tips': self._t(
                        [
                            'أضف وجبة خفيفة بين الوجبات الرئيسية',
                            'تناول المكسرات والفواكه المجففة',
                            'اشرب الحليب كامل الدسم',
                            'أضف زيت زيتون إلى السلطة'
                        ],
                        [
                            'Add a snack between main meals',
                            'Eat nuts and dried fruits',
                            'Drink full-fat milk',
                            'Add olive oil to salad'
                        ]
                    )
                })
        
        return {
            'weight': weight,
            'bmr': int(bmr),
            'daily_activity_burn': int(daily_activity),
            'total_daily_burn': int(total_daily_burn),
            'avg_daily_intake': int(avg_daily_intake),
            'deficit': int(total_daily_burn - avg_daily_intake),
            'alerts': alerts,
            'recommendations': recommendations
        }
    
    def analyze_pulse_pressure(self):
        """
        تحليل متقدم لضغط النبض (Pulse Pressure)
        """
        latest = HealthStatus.objects.filter(
            user=self.user
        ).order_by('-recorded_at').first()
        
        if not latest or not latest.systolic_pressure or not latest.diastolic_pressure:
            return {'status': 'insufficient_data'}
        
        systolic = latest.systolic_pressure
        diastolic = latest.diastolic_pressure
        pulse_pressure = systolic - diastolic
        
        # تحليل جودة النوم
        last_sleep = Sleep.objects.filter(
            user=self.user,
            sleep_end__date=self.today
        ).first()
        
        # تحليل الإجهاد من خلال المزاج
        recent_mood = MoodEntry.objects.filter(
            user=self.user,
            entry_time__date__gte=self.week_ago
        ).order_by('-entry_time')[:3]
        
        stressed_days = sum(1 for m in recent_mood if m.mood in ['Stressed', 'Anxious'])
        
        alert = None
        severity = 'normal'
        
        if pulse_pressure < 15:
            severity = 'critical'
            alert = {
                'type': 'pulse_pressure_critical',
                'severity': 'critical',
                'message': self._t(
                    '🚨 خطر: فرق ضغط النبض منخفض جداً!',
                    '🚨 Critical: Pulse pressure is very low!'
                ),
                'details': self._t(
                    f'الفرق بين الضغط الانقباضي ({systolic}) والانبساطي ({diastolic}) هو {pulse_pressure} مم زئبق فقط',
                    f'The difference between systolic ({systolic}) and diastolic ({diastolic}) is only {pulse_pressure} mmHg'
                ),
                'normal_range': self._t('الطبيعي 40-60 مم زئبق', 'Normal range: 40-60 mmHg'),
                'causes': [],
                'recommendations': [
                    self._t('استشر طبيباً فوراً', 'Consult a doctor immediately')
                ]
            }
            
            # تحليل الأسباب المحتملة
            if last_sleep and float(last_sleep.duration_hours) < 6:
                alert['causes'].append(
                    self._t('قلة النوم (قد تسبب إجهاد القلب)', 'Lack of sleep (may cause heart strain)')
                )
                alert['recommendations'].append(
                    self._t('حاول النوم 7-8 ساعات', 'Try to sleep 7-8 hours')
                )
            
            if stressed_days >= 2:
                alert['causes'].append(
                    self._t('الإجهاد المزمن (يؤثر على انقباض القلب)', 'Chronic stress (affects heart contraction)')
                )
                alert['recommendations'].append(
                    self._t('مارس تمارين التنفس العميق والتأمل', 'Practice deep breathing and meditation')
                )
            
            if not alert['causes']:
                alert['causes'].append(
                    self._t('قد يكون بسبب ضعف عضلة القلب أو مشاكل في الصمامات', 'May be due to heart muscle weakness or valve problems')
                )
                alert['recommendations'].append(
                    self._t('فحص القلب بالموجات الصوتية (Echocardiogram)', 'Echocardiogram')
                )
                
        elif pulse_pressure < 30:
            severity = 'warning'
            alert = {
                'type': 'pulse_pressure_low',
                'severity': 'warning',
                'message': self._t('⚠️ فرق ضغط النبض منخفض', '⚠️ Pulse pressure is low'),
                'details': self._t(
                    f'الفرق بين الضغط الانقباضي ({systolic}) والانبساطي ({diastolic}) هو {pulse_pressure} مم زئبق',
                    f'The difference between systolic ({systolic}) and diastolic ({diastolic}) is {pulse_pressure} mmHg'
                ),
                'normal_range': self._t('الطبيعي 40-60 مم زئبق', 'Normal range: 40-60 mmHg'),
                'causes': [],
                'recommendations': []
            }
            
            if last_sleep and float(last_sleep.duration_hours) < 6:
                alert['causes'].append(
                    self._t('قد يكون بسبب قلة النوم', 'May be due to lack of sleep')
                )
                alert['recommendations'].append(
                    self._t('حسن جودة نومك', 'Improve your sleep quality')
                )
            
            if stressed_days >= 2:
                alert['causes'].append(
                    self._t('قد يكون بسبب الإجهاد', 'May be due to stress')
                )
                alert['recommendations'].append(
                    self._t('جرب تمارين الاسترخاء', 'Try relaxation exercises')
                )
        
        return {
            'systolic': systolic,
            'diastolic': diastolic,
            'pulse_pressure': pulse_pressure,
            'severity': severity,
            'alert': alert,
            'sleep_hours': float(last_sleep.duration_hours) if last_sleep else None,
            'stressed_days': stressed_days
        }
    
    def analyze_pre_exercise_risk(self):
        """
        تحليل مخاطر ممارسة الرياضة بناءً على السكر والضغط
        """
        latest = HealthStatus.objects.filter(
            user=self.user
        ).order_by('-recorded_at').first()
        
        if not latest:
            return {'status': 'insufficient_data'}
        
        glucose = latest.blood_glucose
        systolic = latest.systolic_pressure
        diastolic = latest.diastolic_pressure
        
        # هل هناك نشاط مخطط له اليوم؟
        has_activity_today = PhysicalActivity.objects.filter(
            user=self.user,
            start_time__date=self.today
        ).exists()
        
        # نوع النشاط المتوقع (آخر نشاط مسجل)
        last_activity = PhysicalActivity.objects.filter(
            user=self.user
        ).order_by('-start_time').first()
        
        recommendations = []
        
        if glucose and glucose < 100 and has_activity_today:
            glucose = float(glucose)
            # خطر انخفاض السكر أثناء التمرين
            if glucose < 80:
                recommendations.append({
                    'type': 'critical',
                    'icon': '🚨',
                    'title': self._t('خطر انخفاض السكر', 'Low Blood Sugar Risk'),
                    'message': self._t(
                        'سكر الدم منخفض قبل التمرين',
                        'Blood sugar is low before exercise'
                    ),
                    'details': self._t(
                        f'نسبة السكر {glucose} mg/dL قد تنخفض أكثر أثناء الركض',
                        f'Blood sugar {glucose} mg/dL may drop further during exercise'
                    ),
                    'advice': self._t(
                        'تناول وجبة خفيفة تحتوي على كربوهيدرات قبل التمرين بـ 30 دقيقة',
                        'Eat a light carbohydrate-rich meal 30 minutes before exercise'
                    ),
                    'food_suggestions': self._t(
                        ['موزة', 'تمر (3-4 حبات)', 'عصير فواكه', 'شريحة توست مع عسل'],
                        ['Banana', 'Dates (3-4 pieces)', 'Fruit juice', 'Toast with honey']
                    )
                })
            elif glucose < 100:
                recommendations.append({
                    'type': 'warning',
                    'icon': '⚠️',
                    'title': self._t('احتمال انخفاض السكر', 'Possible Low Blood Sugar'),
                    'message': self._t(
                        'سكر الدم في الحد الأدنى',
                        'Blood sugar is at minimum level'
                    ),
                    'details': self._t(
                        f'نسبة السكر {glucose} mg/dL قريبة من الحد المنخفض',
                        f'Blood sugar {glucose} mg/dL is close to low threshold'
                    ),
                    'advice': self._t(
                        'تناول وجبة خفيفة قبل الركض لتجنب الدوخة',
                        'Eat a light snack before exercise to avoid dizziness'
                    ),
                    'food_suggestions': self._t(
                        ['موزة', 'تمر', 'تفاحة'],
                        ['Banana', 'Dates', 'Apple']
                    )
                })
        
        # تحليل ضغط الدم
        if systolic and diastolic:
            if systolic > 140 or diastolic > 90:
                recommendations.append({
                    'type': 'warning',
                    'icon': '❤️',
                    'title': self._t('ضغط الدم مرتفع', 'High Blood Pressure'),
                    'message': self._t(
                        'ضغطك مرتفع للتمرين المكثف',
                        'Your blood pressure is high for intense exercise'
                    ),
                    'details': self._t(
                        f'{systolic}/{diastolic} - يفضل تمارين خفيفة',
                        f'{systolic}/{diastolic} - prefer light exercises'
                    ),
                    'advice': self._t(
                        'مارس المشي بدلاً من الركض',
                        'Try walking instead of running'
                    ),
                    'alternative': self._t('🚶‍♂️ مشي لمدة 30 دقيقة', '🚶‍♂️ 30-minute walk')
                })
            elif systolic < 90 or diastolic < 60:
                recommendations.append({
                    'type': 'warning',
                    'icon': '💓',
                    'title': self._t('ضغط الدم منخفض', 'Low Blood Pressure'),
                    'message': self._t(
                        'ضغطك منخفض، قد تشعر بدوخة',
                        'Your blood pressure is low, you may feel dizzy'
                    ),
                    'details': self._t(
                        f'{systolic}/{diastolic} - اشرب ماء كافياً',
                        f'{systolic}/{diastolic} - drink enough water'
                    ),
                    'advice': self._t(
                        'تأكد من شرب الماء قبل التمرين',
                        'Make sure to drink water before exercise'
                    ),
                    'tips': self._t(
                        ['اشرب 500 مل ماء', 'تناول وجبة خفيفة مالحة'],
                        ['Drink 500ml water', 'Eat a light salty snack']
                    )
                })
        
        return {
            'glucose': float(glucose) if glucose else None,
            'blood_pressure': f"{systolic}/{diastolic}" if systolic and diastolic else None,
            'has_activity_today': has_activity_today,
            'last_activity_type': last_activity.activity_type if last_activity else None,
            'recommendations': recommendations
        }
    
    def analyze_activity_nutrition(self):
        """
        تحليل العلاقة بين النشاط البدني والتغذية
        """
        # جلب آخر 7 أيام
        activities = PhysicalActivity.objects.filter(
            user=self.user,
            start_time__date__gte=self.week_ago
        ).order_by('-start_time')
        
        if not activities.exists():
            return {
                'status': 'insufficient_data', 
                'message': self._t('لا توجد أنشطة كافية', 'Insufficient activity data')
            }
        
        activity_days = activities.values('start_time__date').annotate(
            total_duration=Sum('duration_minutes'),
            total_calories=Sum('calories_burned')
        )
        
        analysis = []
        
        for day in activity_days:
            date = day['start_time__date']
            
            # ماذا أكل في هذا اليوم؟
            meals = Meal.objects.filter(
                user=self.user,
                meal_time__date=date
            )
            
            total_protein = meals.aggregate(Sum('total_protein'))['total_protein__sum'] or 0
            total_calories = meals.aggregate(Sum('total_calories'))['total_calories__sum'] or 0
            
            # هل كان هناك توازن؟
            calories_burned = day['total_calories'] or 0
            calories_consumed = total_calories
            
            net_calories = calories_consumed - calories_burned
            
            if net_calories < -500 and total_protein < 50:
                analysis.append({
                    'date': date,
                    'warning': True,
                    'message': self._t(
                        '⚠️ عجز حراري كبير مع بروتين منخفض',
                        '⚠️ Large calorie deficit with low protein'
                    ),
                    'details': self._t(
                        f'حرقت {calories_burned} سعرة وأكلت {total_protein:.0f}g بروتين فقط',
                        f'You burned {calories_burned} calories but ate only {total_protein:.0f}g protein'
                    ),
                    'recommendation': self._t(
                        'قد تخسر كتلة عضلية، زد البروتين بعد التمرين',
                        'You may lose muscle mass, increase protein after exercise'
                    )
                })
            elif net_calories > 500 and total_protein > 80:
                analysis.append({
                    'date': date,
                    'insight': True,
                    'message': self._t(
                        '💪 يوم ممتاز لبناء العضلات',
                        '💪 Excellent day for muscle building'
                    ),
                    'details': self._t(
                        f'فائض {net_calories} سعرة مع {total_protein:.0f}g بروتين',
                        f'Surplus {net_calories} calories with {total_protein:.0f}g protein'
                    ),
                    'recommendation': self._t(
                        'استمر بهذا النظام',
                        'Continue this pattern'
                    )
                })
        
        return {
            'total_activities': activities.count(),
            'analysis': analysis,
            'summary': self.summarize_activity_nutrition(analysis)
        }
    
    def analyze_sleep_mood(self):
        """
        تحليل تأثير النوم على الحالة المزاجية
        """
        sleep_records = Sleep.objects.filter(
            user=self.user,
            sleep_start__date__gte=self.week_ago
        ).order_by('-sleep_start')
        
        if not sleep_records.exists():
            return {'status': 'insufficient_data'}
        
        correlation = []
        
        for sleep in sleep_records:
            sleep_date = sleep.sleep_start.date()
            next_day = sleep_date + timedelta(days=1)
            
            # مزاج اليوم التالي
            next_day_mood = MoodEntry.objects.filter(
                user=self.user,
                entry_time__date=next_day
            ).first()
            
            if next_day_mood:
                hours = float(sleep.duration_hours) if sleep.duration_hours else 0
                
                if hours < 6 and next_day_mood.mood in ['Stressed', 'Anxious', 'Sad']:
                    correlation.append({
                        'date': sleep_date,
                        'pattern': self._t('قلة النوم → مزاج سيء', 'Lack of sleep → Bad mood'),
                        'sleep_hours': hours,
                        'mood': next_day_mood.mood,
                        'confidence': 0.85
                    })
                elif hours > 8 and next_day_mood.mood in ['Excellent', 'Good']:
                    correlation.append({
                        'date': sleep_date,
                        'pattern': self._t('نوم كافٍ → مزاج جيد', 'Good sleep → Good mood'),
                        'sleep_hours': hours,
                        'mood': next_day_mood.mood,
                        'confidence': 0.92
                    })
        
        # حساب متوسط النوم لكل مزاج
        mood_sleep_avg = {}
        for mood in ['Excellent', 'Good', 'Neutral', 'Stressed', 'Anxious', 'Sad']:
            mood_days = MoodEntry.objects.filter(
                user=self.user,
                mood=mood,
                entry_time__date__gte=self.week_ago
            ).values_list('entry_time__date', flat=True)
            
            if mood_days:
                # نوم الليلة السابقة
                prev_nights = Sleep.objects.filter(
                    user=self.user,
                    sleep_end__date__in=mood_days
                )
                avg_sleep = prev_nights.aggregate(Avg('duration_hours'))['duration_hours__avg']
                if avg_sleep:
                    mood_sleep_avg[mood] = round(float(avg_sleep), 1)
        
        return {
            'correlations': correlation,
            'mood_sleep_average': mood_sleep_avg,
            'recommendation': self.generate_sleep_recommendation(mood_sleep_avg)
        }
    
    def analyze_weight_trends(self):
        """
        تحليل اتجاهات الوزن مع العوامل المؤثرة
        """
        health_records = HealthStatus.objects.filter(
            user=self.user,
            weight_kg__isnull=False
        ).order_by('recorded_at')
        
        if health_records.count() < 2:
            return {'trend': 'insufficient_data'}
        
        first = health_records.first()
        last = health_records.last()
        
        weight_change = float(last.weight_kg) - float(first.weight_kg)
        days_diff = (last.recorded_at.date() - first.recorded_at.date()).days
        
        if days_diff > 0:
            daily_rate = weight_change / days_diff
            
            # تحليل العوامل المؤثرة
            factors = []
            
            # هل مارس الرياضة كفاية؟
            total_activity = PhysicalActivity.objects.filter(
                user=self.user,
                start_time__date__range=[first.recorded_at.date(), last.recorded_at.date()]
            ).aggregate(Sum('duration_minutes'))['duration_minutes__sum'] or 0
            
            avg_daily_activity = total_activity / days_diff if days_diff > 0 else 0
            
            if avg_daily_activity < 15 and weight_change > 0:
                factors.append({
                    'factor': self._t('قلة النشاط', 'Low activity'),
                    'impact': self._t('قد يكون سبب زيادة الوزن', 'May be causing weight gain')
                })
            elif avg_daily_activity > 30 and weight_change < 0:
                factors.append({
                    'factor': self._t('النشاط المنتظم', 'Regular activity'),
                    'impact': self._t(
                        f'يساعد في خسارة {abs(weight_change):.1f} كجم',
                        f'Helps lose {abs(weight_change):.1f} kg'
                    )
                })
            
            # تحليل التغذية
            avg_calories = Meal.objects.filter(
                user=self.user,
                meal_time__date__range=[first.recorded_at.date(), last.recorded_at.date()]
            ).aggregate(Avg('total_calories'))['total_calories__avg'] or 0
            
            if avg_calories > 2500 and weight_change > 0:
                factors.append({
                    'factor': self._t('سعرات حرارية عالية', 'High calories'),
                    'impact': self._t(
                        f'متوسط {avg_calories:.0f} سعرة/يوم',
                        f'Average {avg_calories:.0f} calories/day'
                    )
                })
            elif avg_calories < 1500 and weight_change < 0:
                factors.append({
                    'factor': self._t('نظام غذائي منخفض', 'Low calorie diet'),
                    'impact': self._t(
                        'قد يكون قاسياً على المدى الطويل',
                        'May be unsustainable long-term'
                    )
                })
            
            return {
                'start_weight': float(first.weight_kg),
                'current_weight': float(last.weight_kg),
                'change': round(weight_change, 1),
                'daily_rate': round(daily_rate * 7, 1),  # أسبوعياً
                'days_analyzed': days_diff,
                'factors': factors,
                'trend': self._t('زيادة', 'Increasing') if weight_change > 0 else self._t('نقصان', 'Decreasing') if weight_change < 0 else self._t('ثبات', 'Stable'),
                'prediction': self.predict_weight(weight_change, daily_rate, days_diff)
            }
    
    def analyze_blood_pressure(self):
        """
        تحليل متقدم لضغط الدم
        """
        records = HealthStatus.objects.filter(
            user=self.user,
            systolic_pressure__isnull=False,
            diastolic_pressure__isnull=False
        ).order_by('-recorded_at')[:10]
        
        if records.count() < 3:
            return {'status': 'insufficient_data'}
        
        # تحليل التغيرات
        changes = []
        for i in range(len(records) - 1):
            current = records[i]
            previous = records[i + 1]
            
            sys_change = current.systolic_pressure - previous.systolic_pressure
            dia_change = current.diastolic_pressure - previous.diastolic_pressure
            
            # هل هناك علاقة مع النوم؟
            sleep_before = Sleep.objects.filter(
                user=self.user,
                sleep_end__date=current.recorded_at.date()
            ).first()
            
            if sleep_before and sleep_before.duration_hours:
                if float(sleep_before.duration_hours) < 6 and sys_change > 5:
                    changes.append({
                        'date': current.recorded_at.date(),
                        'pattern': self._t('قلة النوم → ارتفاع الضغط', 'Lack of sleep → High pressure'),
                        'sleep': float(sleep_before.duration_hours),
                        'pressure_increase': sys_change
                    })
        
        # تحليل متوسط الضغط
        avg_sys = records.aggregate(Avg('systolic_pressure'))['systolic_pressure__avg']
        avg_dia = records.aggregate(Avg('diastolic_pressure'))['diastolic_pressure__avg']
        
        category = self.classify_blood_pressure(avg_sys, avg_dia)
        
        return {
            'average': f"{avg_sys:.0f}/{avg_dia:.0f}",
            'category': category,
            'patterns': changes,
            'recommendation': self.get_bp_recommendation(avg_sys, avg_dia, changes)
        }
    
    def analyze_glucose_risks(self):
        """
        تقييم مخاطر السكر والتنبؤ بالمشكلات
        """
        records = HealthStatus.objects.filter(
            user=self.user,
            blood_glucose__isnull=False
        ).order_by('-recorded_at')[:7]
        
        if records.count() < 2:
            return {'status': 'insufficient_data'}
        
        glucose_values = [float(r.blood_glucose) for r in records if r.blood_glucose]
        
        if not glucose_values:
            return {'status': 'no_data'}
        
        avg_glucose = sum(glucose_values) / len(glucose_values)
        max_glucose = max(glucose_values)
        min_glucose = min(glucose_values)
        
        # هل هناك اتجاه تصاعدي؟
        trend = glucose_values[0] - glucose_values[-1] if len(glucose_values) > 1 else 0
        
        alerts = []
        
        if max_glucose > 140:
            alerts.append({
                'severity': 'high',
                'message': self._t('⚠️ هناك قراءات سكر مرتفعة', '⚠️ There are high glucose readings'),
                'details': self._t(
                    f'أعلى قراءة: {max_glucose:.0f} mg/dL',
                    f'Highest reading: {max_glucose:.0f} mg/dL'
                ),
                'recommendation': self._t(
                    'راجع نظامك الغذائي',
                    'Review your diet'
                )
            })
        
        if min_glucose < 70:
            alerts.append({
                'severity': 'critical',
                'message': self._t('🚨 إنخفاض حاد في السكر', '🚨 Severe drop in glucose'),
                'details': self._t(
                    f'أقل قراءة: {min_glucose:.0f} mg/dL',
                    f'Lowest reading: {min_glucose:.0f} mg/dL'
                ),
                'recommendation': self._t(
                    'احمل معك مصدر سكر دائماً',
                    'Always carry a sugar source'
                )
            })
        
        if trend > 10:
            alerts.append({
                'severity': 'warning',
                'message': self._t('📈 اتجاه تصاعدي في السكر', '📈 Upward trend in glucose'),
                'details': self._t(
                    f'ارتفاع بمعدل {trend:.0f} mg/dL خلال أسبوع',
                    f'Increase of {trend:.0f} mg/dL over a week'
                ),
                'recommendation': self._t(
                    'قد تحتاج لفحص HbA1c',
                    'You may need HbA1c test'
                )
            })
        
        # التنبؤ بالمخاطر المستقبلية
        risk_score = self.calculate_diabetes_risk(avg_glucose, max_glucose, trend)
        
        return {
            'average': round(avg_glucose, 1),
            'range': f"{min_glucose:.0f} - {max_glucose:.0f}",
            'trend': self._t('تصاعدي', 'Upward') if trend > 5 else self._t('تنازلي', 'Downward') if trend < -5 else self._t('مستقر', 'Stable'),
            'alerts': alerts,
            'risk_score': risk_score,
            'risk_level': self._t('منخفض', 'Low') if risk_score < 30 else self._t('متوسط', 'Medium') if risk_score < 60 else self._t('مرتفع', 'High')
        }
    
    def generate_holistic_recommendations(self):
        """
        توليد توصيات شاملة تربط كل العوامل
        """
        recommendations = []
        
        # 1. جلب آخر البيانات
        latest = HealthStatus.objects.filter(user=self.user).order_by('-recorded_at').first()
        if not latest:
            return []
        
        weight = latest.weight_kg
        glucose = latest.blood_glucose
        systolic = latest.systolic_pressure
        diastolic = latest.diastolic_pressure
        
        # 2. نشاط اليوم
        today_activity = PhysicalActivity.objects.filter(
            user=self.user,
            start_time__date=self.today
        ).exists()
        
        # 3. نوم البارحة
        last_sleep = Sleep.objects.filter(
            user=self.user,
            sleep_end__date=self.today
        ).first()
        
        # 4. وجبات اليوم
        today_meals = Meal.objects.filter(
            user=self.user,
            meal_time__date=self.today
        )
        
        total_protein = today_meals.aggregate(Sum('total_protein'))['total_protein__sum'] or 0
        
        # توليد التوصيات المتقاطعة
        
        # حالة 1: وزن منخفض + نشاط عالي
        if weight and weight < 55 and today_activity:
            weight = float(weight)
            recommendations.append({
                'icon': '⚡',
                'title': self._t('توازن الوزن والنشاط', 'Weight & Activity Balance'),
                'message': self._t('وزنك منخفض مع نشاط رياضي', 'Low weight with physical activity'),
                'details': self._t('قد تخسر كتلة عضلية بدلاً من الدهون', 'You may lose muscle mass instead of fat'),
                'advice': self._t('تناول وجبة غنية بالبروتين بعد التمرين مباشرة', 'Eat a protein-rich meal immediately after exercise'),
                'priority': 'high'
            })
        
        # حالة 2: ضغط منخفض + سكر منخفض
        if systolic and systolic < 100 and glucose and glucose < 80:
            glucose = float(glucose)
            recommendations.append({
                'icon': '🫀',
                'title': self._t('علامات الإرهاق', 'Fatigue Signs'),
                'message': self._t('ضغط وسكر منخفضان معاً', 'Low pressure and glucose together'),
                'details': self._t('قد يكون بسبب إجهاد أو وجبات غير كافية', 'May be due to stress or insufficient meals'),
                'advice': self._t('تناول وجبة متوازنة واسترح قليلاً', 'Eat a balanced meal and rest'),
                'priority': 'high'
            })
        
        # حالة 3: نوم قليل + مزاج سيء متوقع
        if last_sleep and float(last_sleep.duration_hours) < 6:
            recommendations.append({
                'icon': '😴',
                'title': self._t('تأثير النوم على يومك', 'Sleep Impact on Your Day'),
                'message': self._t(
                    f'نمتَ {float(last_sleep.duration_hours):.1f} ساعات فقط',
                    f'You slept only {float(last_sleep.duration_hours):.1f} hours'
                ),
                'details': self._t('قلة النوم تؤثر على التركيز والمزاج', 'Lack of sleep affects focus and mood'),
                'advice': self._t('خذ قيلولة 20 دقيقة بعد الظهر', 'Take a 20-minute nap in the afternoon'),
                'priority': 'medium'
            })
        
        # حالة 4: بروتين منخفض + نشاط عالي
        if total_protein < 30 and today_activity:
            recommendations.append({
                'icon': '💪',
                'title': self._t('البروتين والطاقة', 'Protein & Energy'),
                'message': self._t(f'بروتينك اليوم {total_protein:.0f}g فقط', f'Only {total_protein:.0f}g protein today'),
                'details': self._t('قد تشعر بإرهاق سريع في التمرين', 'You may feel quick fatigue during exercise'),
                'advice': self._t('زد البروتين في وجبتك القادمة (بيض، دجاج، عدس)', 'Increase protein in your next meal (eggs, chicken, lentils)'),
                'priority': 'medium'
            })
        
        # حالة 5: ضغط انبساطي مرتفع مع سكر مرتفع
        if diastolic and diastolic > 85 and glucose and glucose > 120:
            glucose = float(glucose)
            recommendations.append({
                'icon': '❤️',
                'title': self._t('علامات استقلابية', 'Metabolic Signs'),
                'message': self._t('ارتفاع في الضغط الانبساطي والسكر', 'High diastolic pressure and glucose'),
                'details': self._t('قد يشير لمقاومة الأنسولين', 'May indicate insulin resistance'),
                'advice': self._t('قلل السكريات وزد النشاط البدني', 'Reduce sugars and increase physical activity'),
                'priority': 'high'
            })
        
        return recommendations
    
    def generate_predictive_alerts(self):
        """
        تنبؤات بالمشكلات الصحية المستقبلية
        """
        alerts = []
        
        # 1. هل سكر الدم في ارتفاع مستمر؟
        glucose_records = HealthStatus.objects.filter(
            user=self.user,
            blood_glucose__isnull=False
        ).order_by('recorded_at')[:5]
        
        if glucose_records.count() >= 3:
            values = [float(r.blood_glucose) for r in glucose_records]
            first_value = values[0] if values else 0
            last_value = values[-1] if values else 0
            
            if first_value < last_value - 20:
                alerts.append({
                    'type': 'glucose_trend',
                    'severity': 'warning',
                    'title': self._t('📊 ارتفاع تدريجي في السكر', '📊 Gradual Rise in Glucose'),
                    'prediction': self._t(
                        'إذا استمر الاتجاه، قد تصل لمرحلة ما قبل السكري خلال 3 أشهر',
                        'If trend continues, you may reach pre-diabetes in 3 months'
                    ),
                    'probability': '65%',
                    'action': self._t(
                        'قلل الكربوهيدرات البسيطة وامش 30 دقيقة يومياً',
                        'Reduce simple carbs and walk 30 minutes daily'
                    )
                })
        
        # 2. هل الوزن في زيادة سريعة؟
        weight_records = HealthStatus.objects.filter(
            user=self.user,
            weight_kg__isnull=False
        ).order_by('recorded_at')[:5]
        
        if weight_records.count() >= 2:
            weight_list = list(weight_records)
            
            first = float(weight_list[0].weight_kg)
            last = float(weight_list[-1].weight_kg)
            
            first_date = weight_list[0].recorded_at.date()
            last_date = weight_list[-1].recorded_at.date()
            days = (last_date - first_date).days
            
            if days > 0:
                monthly_rate = ((last - first) / days) * 30
                if monthly_rate > 2:
                    alerts.append({
                        'type': 'weight_trend',
                        'severity': 'warning',
                        'title': self._t('⚖️ زيادة سريعة في الوزن', '⚖️ Rapid Weight Gain'),
                        'prediction': self._t(
                            f'قد تزيد {monthly_rate:.1f} كجم خلال شهر إذا استمر الوضع',
                            f'You may gain {monthly_rate:.1f} kg in a month if this continues'
                        ),
                        'probability': '80%',
                        'action': self._t(
                            'سجل طعامك وراجع السعرات الحرارية',
                            'Log your food and review calories'
                        )
                    })
                elif monthly_rate < -2:
                    alerts.append({
                        'type': 'weight_trend',
                        'severity': 'info',
                        'title': self._t('⚖️ خسارة وزن سريعة', '⚖️ Rapid Weight Loss'),
                        'prediction': self._t(
                            f'قد تخسر {abs(monthly_rate):.1f} كجم خلال شهر',
                            f'You may lose {abs(monthly_rate):.1f} kg in a month'
                        ),
                        'probability': '75%',
                        'action': self._t(
                            'تأكد من الحصول على بروتين كافٍ',
                            'Ensure adequate protein intake'
                        )
                    })
        
        # 3. هل نمط النوم مضطرب؟
        sleep_records = Sleep.objects.filter(
            user=self.user,
            sleep_start__date__gte=self.week_ago
        )
        
        if sleep_records.count() >= 3:
            inconsistent = False
            for sleep in sleep_records:
                if sleep.duration_hours and (float(sleep.duration_hours) < 5 or float(sleep.duration_hours) > 10):
                    inconsistent = True
                    break
            
            if inconsistent:
                alerts.append({
                    'type': 'sleep_pattern',
                    'severity': 'info',
                    'title': self._t('😴 نمط نوم غير منتظم', '😴 Irregular Sleep Pattern'),
                    'prediction': self._t(
                        'قد تعاني من الأرق أو اضطراب النوم',
                        'You may have insomnia or sleep disorder'
                    ),
                    'probability': '55%',
                    'action': self._t(
                        'حاول النوم في وقت ثابت يومياً',
                        'Try to sleep at a fixed time daily'
                    )
                })
        
        return alerts
    
    def summarize_activity_nutrition(self, analysis):
        """تلخيص تحليل النشاط والتغذية"""
        warnings = sum(1 for a in analysis if a.get('warning'))
        insights = sum(1 for a in analysis if a.get('insight'))
        
        if warnings > insights:
            return self._t('⚠️ تحتاج لتحسين التوازن بين طعامك ونشاطك', '⚠️ You need to balance your food and activity')
        elif insights > warnings:
            return self._t('🌟 نظامك الغذائي متوازن مع نشاطك', '🌟 Your diet is balanced with your activity')
        else:
            return self._t('📊 بيانات كافية للتحليل، استمر بالتسجيل', '📊 Sufficient data for analysis, keep recording')
    
    def generate_sleep_recommendation(self, mood_sleep_avg):
        """توليد توصية نوم بناءً على المزاج"""
        if not mood_sleep_avg:
            return self._t('سجل نومك باستمرار للحصول على توصيات', 'Keep recording your sleep for recommendations')
        
        good_moods = ['Excellent', 'Good']
        bad_moods = ['Stressed', 'Anxious', 'Sad']
        
        good_sleep = [mood_sleep_avg.get(m, 0) for m in good_moods if m in mood_sleep_avg]
        bad_sleep = [mood_sleep_avg.get(m, 0) for m in bad_moods if m in mood_sleep_avg]
        
        if good_sleep and bad_sleep:
            avg_good = sum(good_sleep) / len(good_sleep)
            avg_bad = sum(bad_sleep) / len(bad_sleep)
            
            if avg_good > avg_bad:
                return self._t(
                    f'💤 النوم {avg_good:.1f} ساعات يرتبط بمزاجك الجيد',
                    f'💤 Sleeping {avg_good:.1f} hours is linked to your good mood'
                )
            else:
                return self._t(
                    f'🌙 حاول النوم {avg_good:.1f} ساعات لمزاج أفضل',
                    f'🌙 Try sleeping {avg_good:.1f} hours for better mood'
                )
        
        return self._t('استمر بتسجيل نومك ومزاجك', 'Keep recording your sleep and mood')
    
    def classify_blood_pressure(self, sys, dia):
        """تصنيف ضغط الدم"""
        if not sys or not dia:
            return self._t('غير معروف', 'Unknown')
        
        if sys < 120 and dia < 80:
            return self._t('مثالي', 'Ideal')
        elif sys < 130 and dia < 80:
            return self._t('طبيعي', 'Normal')
        elif sys < 140 or dia < 90:
            return self._t('مرتفع - المرحلة 1', 'High - Stage 1')
        elif sys >= 140 or dia >= 90:
            return self._t('مرتفع - المرحلة 2', 'High - Stage 2')
        else:
            return self._t('غير مصنف', 'Unclassified')
    
    def get_bp_recommendation(self, sys, dia, patterns):
        """توصية لضغط الدم"""
        if not sys or not dia:
            return self._t('لا توجد بيانات كافية', 'Insufficient data')
        
        if patterns:
            return self._t(
                'نمط واضح: قلة النوم ترفع ضغطك. حاول النوم 7-8 ساعات',
                'Clear pattern: Lack of sleep raises your pressure. Try sleeping 7-8 hours'
            )
        
        category = self.classify_blood_pressure(sys, dia)
        
        if category in [self._t('مثالي', 'Ideal'), 'Ideal']:
            return self._t('ضغطك ممتاز، استمر بنظامك الصحي', 'Your pressure is excellent, maintain your healthy routine')
        elif category in [self._t('طبيعي', 'Normal'), 'Normal']:
            return self._t('ضغطك طبيعي، حافظ على نشاطك', 'Your pressure is normal, maintain your activity')
        elif category in [self._t('مرتفع - المرحلة 1', 'High - Stage 1'), 'High - Stage 1']:
            return self._t('ضغطك بداية ارتفاع، جرب تمارين التنفس والمشي', 'Your pressure is starting to rise, try breathing exercises and walking')
        else:
            return self._t('ضغطك مرتفع، استشر طبيباً', 'Your pressure is high, consult a doctor')
    
    def calculate_diabetes_risk(self, avg, max_val, trend):
        """حساب مخاطر السكري"""
        risk = 0
        
        if avg > 100:
            risk += (avg - 100) * 0.5
        if max_val > 140:
            risk += (max_val - 140) * 2
        if trend > 5:
            risk += trend * 3
        
        return min(100, int(risk))
    
    def predict_weight(self, change, daily_rate, days):
        """التنبؤ بالوزن المستقبلي"""
        if days < 7:
            return self._t('تحتاج لبيانات أكثر للتنبؤ', 'Need more data for prediction')
        
        monthly = daily_rate * 30
        
        if abs(monthly) < 1:
            return self._t('وزنك مستقر، حافظ على نظامك', 'Your weight is stable, maintain your routine')
        elif monthly > 0:
            return self._t(
                f'إذا استمر الوضع، قد تزيد {monthly:.1f} كجم خلال شهر',
                f'If this continues, you may gain {monthly:.1f} kg in a month'
            )
        else:
            return self._t(
                f'إذا استمر الوضع، قد تخسر {abs(monthly):.1f} كجم خلال شهر',
                f'If this continues, you may lose {abs(monthly):.1f} kg in a month'
            )
 