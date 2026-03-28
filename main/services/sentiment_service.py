# services/sentiment_service.py
import os
import requests
import json
import re

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # مجاني وسريع
        
        if not self.api_key:
            print("⚠️ GROQ_API_KEY not found. Using fallback mode.")
    
    def analyze(self, text):
        """تحليل المشاعر في النص باستخدام Groq API"""
        if not self.api_key:
            return self._fallback_response()
        
        prompt = f"""
        أنت محلل مشاعر متخصص. حلل النص التالي وأعد النتيجة بصيغة JSON فقط.
        
        النص: "{text}"
        
        أجب بهذا التنسيق فقط:
        {{"label": "POSITIVE/NEGATIVE/NEUTRAL", "score": 0.95, "sentiment": "إيجابي 😊/سلبي 😞/محايد 😐"}}
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 100
        }
        
        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return {
                        'label': data.get('label', 'NEUTRAL'),
                        'score': data.get('score', 0.5),
                        'sentiment': data.get('sentiment', 'محايد 😐')
                    }
            
            return self._fallback_response()
            
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._fallback_response()
    
    def _fallback_response(self):
        """رد بديل في حالة فشل API"""
        return {
            'label': 'NEUTRAL',
            'score': 0.5,
            'sentiment': 'محايد 😐'
        }
    
    def map_sentiment(self, label):
        """تحويل نتيجة التحليل إلى مشاعر مفهومة"""
        mapping = {
            'POSITIVE': 'إيجابي 😊',
            'NEGATIVE': 'سلبي 😞',
            'NEUTRAL': 'محايد 😐'
        }
        return mapping.get(label, 'محايد 😐')