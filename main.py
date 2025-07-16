import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from datetime import datetime
from dotenv import load_dotenv

# 自作モジュールをインポート
from database import DatabaseManager
from auto_poster import AutoPoster

# 外部モジュールのインポートテスト
try:
    from news_collector import SimpleNewsCollector
    from gemini_writer import GeminiWriter
except ImportError:
    # フォールバック: 簡単な実装
    class SimpleNewsCollector:
        def get_ai_news(self, limit=3):
            return [{
                'title': 'AI技術の最新動向',
                'summary': 'AI技術が急速に発展しています。',
                'url': 'https://example.com/ai-news',
                'source': 'fallback'
            }]

    class GeminiWriter:
        def __init__(self, api_key):
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')

        def generate_blog_post(self, article, max_length=500):
            try:
                prompt = (
                    "以下のニュースを高校生向けに500文字以内で要約してください:\n"
                    f"{article['title']}\n{article['summary']}"
                )
                response = self.model.generate_content(prompt)
                return {
                    'title': article['title'][:50],
                    'content': response.text[:max_length],
                    'hashtags': '#AI #人工知能 #テクノロジー',
                    'source_url': article['url'],
                    'generated_at': datetime.now().isoformat(),
                }
            except Exception as e:
                # フォールバックテキストを返す
                            return {
                     'title': article['title'][:50],
                    'content': (
                         f"{article['title']}\n\n{article['summary']}\n\n"
                       "AI技術の発展により、私たちの生活がより便利になることが期待されています。"
                   )[:max_length],
                   'hashtags': '#AI #人工知能 #テクノロジー',
                     'source_url': article['url'],
                  'generated_at': datetime.now().isoformat(),
                 }
