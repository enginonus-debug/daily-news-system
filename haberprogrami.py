import os
import smtplib
import schedule
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()  # .env dosyasını yükler
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
import requests
from anthropic import Anthropic
import json

# ====== YAPILANDIRMA ======
class Config:
    # E-posta Ayarları
    SENDER_EMAIL = "enginyapayzeka@gmail.com"  # Gönderen mail
    SENDER_PASSWORD = "shwy ngkp eoec jpeg"  # Gmail App Password
    RECIPIENT_EMAIL = "enginonus@gmail.com"  # Alıcı mail (sizin mailiniz)
    
    # API Anahtarları
    NEWS_API_KEY = "70726bb72a6d414db2daeefeb3de1644"  # https://newsapi.org
    ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
    
    # Haber Kategorileri ve Anahtar Kelimeler
    CATEGORIES = {
        "Teknoloji": ["artificial intelligence", "machine learning", "quantum computing", "robotics", "5G", "blockchain"],
        "Finans": ["fintech", "cryptocurrency", "investment", "venture capital", "funding round", "IPO"],
        "Girişimcilik": ["startup", "entrepreneur", "unicorn", "seed funding", "series A", "innovation"],
        "E-Ticaret": ["e-commerce", "online retail", "marketplace", "dropshipping", "shopify", "amazon"],
        "Teknolojik Tarım": ["agritech", "precision agriculture", "vertical farming", "smart farming", "agricultural technology"],
        "İş Fırsatları": ["grant", "subsidy", "business opportunity", "tender", "call for proposals", "funding program"]
    }
    
    # Zamanla Ayarı
    SEND_TIME = "12:00"  # Her gün saat 12:00'da gönder

# ====== HABER TOPLAMA ======
class NewsCollector:
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2/everything"
        
    def fetch_news(self, keywords, max_articles=5):
        """Belirli anahtar kelimelere göre haber topla"""
        all_articles = []
        
        for keyword in keywords:
            params = {
                'q': keyword,
                'apiKey': self.api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': max_articles
            }
            
            try:
                response = requests.get(self.base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    all_articles.extend(articles[:2])  # Her anahtar kelime için 2 haber
            except Exception as e:
                print(f"Haber toplama hatası ({keyword}): {e}")
                
        return all_articles
    
    def collect_all_news(self):
        """Tüm kategorilerden haber topla"""
        categorized_news = {}
        
        for category, keywords in Config.CATEGORIES.items():
            print(f"{category} kategorisi için haberler toplanıyor...")
            articles = self.fetch_news(keywords, max_articles=3)
            categorized_news[category] = articles
            
        return categorized_news

# ====== HABER ANALİZİ VE ÇEVİRİ ======
class NewsAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
    def analyze_and_translate(self, article):
        """Haberi Türkçe'ye çevir ve analiz et"""
        prompt = f"""
Aşağıdaki İngilizce haberi analiz et ve Türkçe'ye çevir:

Başlık: {article.get('title', 'Başlık yok')}
İçerik: {article.get('description', '')}

Lütfen şu formatta yanıt ver:

BAŞLIK: [Türkçe başlık]

DETAYLAR: [Haberin detaylı Türkçe özeti - 2-3 paragraf]

YAPAY ZEKA YORUMU: [Bu haberin teknoloji ve girişimcilik dünyası için önemi, potansiyel etkileri ve fırsatlar hakkında 2-3 cümlelik analiz]
"""
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
        except Exception as e:
            print(f"Analiz hatası: {e}")
            return f"BAŞLIK: {article.get('title', 'Başlık yok')}\n\nDETAYLAR: Çeviri yapılamadı.\n\nYAPAY ZEKA YORUMU: Analiz yapılamadı."

# ====== E-POSTA GÖNDERİMİ ======
class EmailSender:
    def __init__(self):
        self.sender_email = Config.SENDER_EMAIL
        self.sender_password = Config.SENDER_PASSWORD
        self.recipient_email = Config.RECIPIENT_EMAIL
        
    def create_html_email(self, categorized_news, analyzed_news):
        """HTML formatında e-posta oluştur"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .category {{ background: #f4f4f4; margin: 20px 0; padding: 20px; border-radius: 8px; }}
                .category-title {{ color: #667eea; font-size: 24px; margin-bottom: 15px; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
                .news-item {{ background: white; margin: 15px 0; padding: 20px; border-left: 4px solid #764ba2; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .news-title {{ color: #333; font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
                .news-details {{ color: #555; margin: 15px 0; }}
                .news-analysis {{ background: #f0f7ff; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 3px solid #667eea; }}
                .analysis-label {{ color: #667eea; font-weight: bold; margin-bottom: 5px; }}
                .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
                .source {{ color: #999; font-size: 12px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Günlük Teknoloji ve Girişim Haberleri</h1>
                <p>{datetime.now().strftime('%d %B %Y, %A')}</p>
            </div>
        """
        
        for category, articles in categorized_news.items():
            if articles:
                html += f'<div class="category"><h2 class="category-title">📌 {category}</h2>'
                
                for i, article in enumerate(articles[:3]):  # Her kategoriden en fazla 3 haber
                    analyzed = analyzed_news.get(f"{category}_{i}", "")
                    
                    # Analiz edilmiş içeriği parse et
                    parts = analyzed.split('\n\n')
                    title = parts[0].replace('BAŞLIK:', '').strip() if len(parts) > 0 else article.get('title', 'Başlık yok')
                    details = parts[1].replace('DETAYLAR:', '').strip() if len(parts) > 1 else 'Detay yok'
                    analysis = parts[2].replace('YAPAY ZEKA YORUMU:', '').strip() if len(parts) > 2 else 'Analiz yok'
                    
                    html += f"""
                    <div class="news-item">
                        <div class="news-title">{title}</div>
                        <div class="news-details">{details}</div>
                        <div class="news-analysis">
                            <div class="analysis-label">🤖 Yapay Zeka Yorumu:</div>
                            {analysis}
                        </div>
                        <div class="source">Kaynak: {article.get('source', {}).get('name', 'Bilinmeyen')}</div>
                    </div>
                    """
                
                html += '</div>'
        
        html += """
            <div class="footer">
                <p>Bu bülten otomatik olarak oluşturulmuştur.</p>
                <p>© 2025 Günlük Haber Sistemi</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def send_email(self, html_content):
        """E-posta gönder"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📰 Günlük Teknoloji Haberleri - {datetime.now().strftime('%d/%m/%Y')}"
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print(f"✅ E-posta başarıyla gönderildi: {datetime.now()}")
        except Exception as e:
            print(f"❌ E-posta gönderme hatası: {e}")

# ====== ANA UYGULAMA ======
class DailyNewsSystem:
    def __init__(self):
        self.collector = NewsCollector()
        self.analyzer = NewsAnalyzer()
        self.sender = EmailSender()
        
    def run_daily_task(self):
        """Günlük haber toplama ve gönderme görevi"""
        print(f"\n{'='*50}")
        print(f"🚀 Günlük haber toplama başladı: {datetime.now()}")
        print(f"{'='*50}\n")
        
        # 1. Haberleri topla
        categorized_news = self.collector.collect_all_news()
        
        # 2. Haberleri analiz et ve çevir
        analyzed_news = {}
        for category, articles in categorized_news.items():
            for i, article in enumerate(articles[:3]):
                print(f"Analiz ediliyor: {category} - {article.get('title', 'Başlık yok')[:50]}...")
                analyzed = self.analyzer.analyze_and_translate(article)
                analyzed_news[f"{category}_{i}"] = analyzed
        
        # 3. E-posta oluştur ve gönder
        html_content = self.sender.create_html_email(categorized_news, analyzed_news)
        self.sender.send_email(html_content)
        
        print(f"\n{'='*50}")
        print(f"✅ Günlük görev tamamlandı: {datetime.now()}")
        print(f"{'='*50}\n")
    
    def start_scheduler(self):
        """Zamanlanmış görevleri başlat"""
        # Her gün belirli saatte çalıştır
        schedule.every().day.at(Config.SEND_TIME).do(self.run_daily_task)
        
        print(f"⏰ Zamanlayıcı başlatıldı. Her gün saat {Config.SEND_TIME}'de çalışacak.")
        print(f"🔄 Sistem çalışıyor... (Durdurmak için Ctrl+C)")
        
        # İlk testi hemen yap (isteğe bağlı)
        # self.run_daily_task()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et

# ====== PROGRAMI BAŞLAT ======
if __name__ == "__main__":
    system = DailyNewsSystem()
    # system.run_daily_task()  # Test tamamlandı, kapat
    system.start_scheduler()  # Günlük çalışsın