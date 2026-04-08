// services/notification-service.js
const express = require('express');
const cors = require('cors');
const webpush = require('web-push');

const app = express();
const PORT = process.env.PORT || 3003;

// VAPID Keys (من حسابك في Google)
const vapidKeys = {
    publicKey: 'BHlznz8R_5JWZ7C-JtA-kV60tNuqOU4vdW55C9p8iIhU6hJIHiJSH3SpkvYT_0HB81yj_P2Wv0IT5mG_YNmjf4E',
    privateKey: '_QIay_MCjUoCV8S_WPD6uSUuB9F-AMLpkNc445jDTxA'
};

webpush.setVapidDetails(
    'mailto:rin31426@gmail.com',
    vapidKeys.publicKey,
    vapidKeys.privateKey
);

app.use(cors());
app.use(express.json());

// تخزين الاشتراكات (في الإنتاج استخدم Redis أو PostgreSQL)
let subscriptions = {};

// ✅ حفظ اشتراك مستخدم
app.post('/subscribe', (req, res) => {
    const { userId, subscription } = req.body;
    
    if (!userId || !subscription) {
        return res.status(400).json({ error: 'Missing userId or subscription' });
    }
    
    if (!subscriptions[userId]) {
        subscriptions[userId] = [];
    }
    
    // تجنب التكرار
    const exists = subscriptions[userId].some(s => s.endpoint === subscription.endpoint);
    if (!exists) {
        subscriptions[userId].push(subscription);
    }
    
    console.log(`✅ Subscription saved for user ${userId}`);
    res.json({ success: true, total: subscriptions[userId].length });
});

// ✅ إزالة اشتراك
app.post('/unsubscribe', (req, res) => {
    const { userId, endpoint } = req.body;
    
    if (subscriptions[userId]) {
        subscriptions[userId] = subscriptions[userId].filter(s => s.endpoint !== endpoint);
    }
    
    res.json({ success: true });
});

// ✅ إرسال إشعار لمستخدم محدد
app.post('/notify/:userId', async (req, res) => {
    const { userId } = req.params;
    const { title, body, icon, url } = req.body;
    
    const userSubs = subscriptions[userId] || [];
    
    if (userSubs.length === 0) {
        return res.json({ success: true, message: 'No subscriptions for this user', sent: 0 });
    }
    
    const payload = JSON.stringify({
        title: title || 'LivoCare',
        body: body || 'لديك إشعار جديد',
        icon: icon || '/logo192.png',
        url: url || '/dashboard'
    });
    
    const results = await Promise.allSettled(
        userSubs.map(sub => webpush.sendNotification(sub, payload).catch(e => {
            // إذا كان الاشتراك منتهياً، احذفه
            if (e.statusCode === 410) {
                subscriptions[userId] = subscriptions[userId].filter(s => s.endpoint !== sub.endpoint);
            }
            throw e;
        }))
    );
    
    const sent = results.filter(r => r.status === 'fulfilled').length;
    const failed = results.filter(r => r.status === 'rejected').length;
    
    console.log(`📱 Notifications sent to user ${userId}: ${sent} success, ${failed} failed`);
    
    res.json({
        success: true,
        sent,
        failed,
        total: userSubs.length
    });
});

// ✅ إرسال إشعار لجميع المستخدمين (للمسؤول)
app.post('/notify/all', async (req, res) => {
    const { title, body, icon, url } = req.body;
    
    const userIds = Object.keys(subscriptions);
    let totalSent = 0;
    
    for (const userId of userIds) {
        const userSubs = subscriptions[userId] || [];
        const payload = JSON.stringify({ title, body, icon, url });
        
        for (const sub of userSubs) {
            try {
                await webpush.sendNotification(sub, payload);
                totalSent++;
            } catch (e) {
                if (e.statusCode === 410) {
                    subscriptions[userId] = subscriptions[userId].filter(s => s.endpoint !== sub.endpoint);
                }
            }
        }
    }
    
    res.json({ success: true, sent: totalSent, users: userIds.length });
});

// ✅ الحصول على إحصائيات
app.get('/stats', (req, res) => {
    const stats = {};
    for (const [userId, subs] of Object.entries(subscriptions)) {
        stats[userId] = subs.length;
    }
    
    res.json({
        totalUsers: Object.keys(subscriptions).length,
        totalSubscriptions: Object.values(subscriptions).reduce((a, b) => a + b.length, 0),
        details: stats
    });
});

// ✅ مسار الصحة
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Notification Service running on port ${PORT}`);
    console.log(`📱 VAPID Public Key: ${vapidKeys.publicKey.substring(0, 30)}...`);
});