const express = require('express');
const cors = require('cors');
const nodemailer = require('nodemailer');

const app = express();
const PORT = process.env.PORT || 3004;

// إعدادات البريد (استخدم SendGrid أو Gmail)
const transporter = nodemailer.createTransport({
    host: process.env.EMAIL_HOST || 'smtp.sendgrid.net',
    port: parseInt(process.env.EMAIL_PORT) || 587,
    secure: false,
    auth: {
        user: process.env.EMAIL_USER || 'apikey',
        pass: process.env.EMAIL_PASSWORD || ''
    }
});

app.use(cors());
app.use(express.json());

// ✅ مسار الصحة (للتحقق من أن الخدمة تعمل)
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        service: 'email-service',
        timestamp: new Date().toISOString() 
    });
});

// إرسال بريد
app.post('/send', async (req, res) => {
    const { to, subject, message } = req.body;
    
    try {
        await transporter.sendMail({
            from: process.env.FROM_EMAIL || 'noreply@livocare.com',
            to: to,
            subject: subject,
            text: message
        });
        console.log(`📧 Email sent to ${to}: ${subject}`);
        res.json({ success: true });
    } catch (error) {
        console.error('Email error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// مسار ترحيبي بسيط
app.get('/', (req, res) => {
    res.json({ 
        message: 'Email Service is running',
        endpoints: ['POST /send', 'GET /health']
    });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Email Service running on port ${PORT}`);
});