// google-auth-service.js
const express = require('express');
const { OAuth2Client } = require('google-auth-library');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3002;

const googleClient = new OAuth2Client(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

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
            audience: process.env.GOOGLE_CLIENT_ID
        });
        
        const payload = ticket.getPayload();
        
        // ✅ إرسال البيانات إلى خادم Django الرئيسي
        const response = await axios.post(`${process.env.DJANGO_API_URL}/api/auth/google/`, {
            email: payload.email,
            name: payload.name,
            google_id: payload.sub,
            picture: payload.picture
        });
        
        // ✅ تخزين التوكن في localStorage عبر redirect
        res.redirect(`${process.env.FRONTEND_URL}/auth/callback?token=${response.data.access}`);
        
    } catch (error) {
        console.error('Google auth error:', error);
        res.redirect(`${process.env.FRONTEND_URL}/login?error=google_auth_failed`);
    }
});

app.listen(PORT, () => {
    console.log(`✅ Google Auth Service running on port ${PORT}`);
});