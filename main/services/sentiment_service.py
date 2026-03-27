# services/sentiment_service.py
from transformers import pipeline

class SentimentAnalyzer:
    def __init__(self):
        # استخدام نموذج عربي لتحليل المشاعر
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="CAMeL-Lab/bert-base-arabic-camelbert-mix-sentiment"
        )
    
    def analyze(self, text):
        """تحليل المشاعر في النص"""
        try:
            result = self.analyzer(text)[0]
            return {
                'label': result['label'],
                'score': result['score'],
                'sentiment': self.map_sentiment(result['label'])
            }
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {'label': 'NEUTRAL', 'score': 0.5, 'sentiment': 'neutral'}
    
    def map_sentiment(self, label):
        """تحويل نتيجة التحليل إلى مشاعر مفهومة"""
        mapping = {
            'POSITIVE': 'إيجابي 😊',
            'NEGATIVE': 'سلبي 😞',
            'NEUTRAL': 'محايد 😐'
        }
        return mapping.get(label, 'محايد 😐')