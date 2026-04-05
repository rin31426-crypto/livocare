const express = require('express');
const { OAuth2Client } = require('google-auth-library');
const axios = require('axios');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3002;

// ✅ كتابة القيم مباشرة (للتغلب على مشكلة متغيرات البيئة)
const GOOGLE_CLIENT_ID = '1078379162660-79iiq3dsp2hr8sss8n2o5n9j6q3m9h7b.apps.googleusercontent.com';
const GOOGLE_CLIENT_SECRET = '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';
const GOOGLE_REDIRECT_URI = 'https://google-auth-fwz4.onrender.com/auth/google/callback';
const DJANGO_API_URL = 'https://livocare.onrender.com';
const FRONTEND_URL = 'https://livocare-fronend.onrender.com';

const googleClient = new OAuth2Client(
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI
);

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ✅ مسار رئيسي
app.get('/', (req, res) => {
    res.send('Google Auth Service is running! Use /auth/google to login');
});

// ✅ مسار للتحقق من صحة الخدمة
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 1. بدء تسجيل الدخول
app.get('/auth/google', (req, res) => {
    const url = googleClient.generateAuthUrl({
        access_type: 'online',
        scope: ['profile', 'email'],
        state: req.query.state || '/'
    });
    res.redirect(url);
});

// 2. معالجة回调
app.get('/auth/google/callback', async (req, res) => {
    const { code } = req.query;
    
    try {
        const { tokens } = await googleClient.getToken(code);
        const ticket = await googleClient.verifyIdToken({
            idToken: tokens.id_token,
            audience: GOOGLE_CLIENT_ID
        });
        
        const payload = ticket.getPayload();
        
        const response = await axios.post(`${DJANGO_API_URL}/api/auth/google/`, {
            email: payload.email,
            name: payload.name,
            google_id: payload.sub,
            picture: payload.picture
        });
        
        res.redirect(`${FRONTEND_URL}/auth/callback?token=${response.data.access}`);
        
    } catch (error) {
        console.error('Google auth error:', error);
        res.redirect(`${FRONTEND_URL}/login?error=google_auth_failed`);
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Google Auth Service running on port ${PORT}`);
    console.log(`🔑 Using Google Client ID: ${GOOGLE_CLIENT_ID.substring(0, 20)}...`);
});