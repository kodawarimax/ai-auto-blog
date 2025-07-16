#!/usr/bin/env python3
"""
完全自動 AI 投稿システム ― エントリポイント
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

# プロジェクトルートをパスに追加
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 環境変数ロード
from dotenv import load_dotenv
load_dotenv()

# 自作モジュール
from database import DatabaseManager
from auto_poster import AutoPoster

# optional モジュール
try:
    from news_collector import SimpleNewsCollector
    from gemini_writer import GeminiWriter
except ImportError:
    # フォールバック実装
    class SimpleNewsCollector:
        def get_ai_news(self, limit: int = 3) -> List[Dict]:
            return [{
                "title": "AI 技術の最新動向",
                "summary": "AI 技術が急速に発展しています。",
                "url": "https://example.com/ai-news",
                "source": "fallback"
            }]

    class GeminiWriter:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        def generate_blog_post(self, article: Dict, max_length: int = 500) -> Dict:
            text = (
                f"{article['title']}\n\n{article['summary']}\n\n"
                "AI 技術の発展により、私たちの生活がより便利になることが期待されています。"
            )
            return {
                "title": article["title"][:50],
                "content": text[:max_length],
                "hashtags": "#AI #人工知能 #テクノロジー",
                "source_url": article["url"],
                "generated_at": datetime.now().isoformat(),
            }

class AutoAIBlogSystem:
    REQUIRED_ENV_VARS = [
        "GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY",
        "BLOG_URL", "BLOG_USERNAME", "BLOG_PASSWORD"
    ]

    def __init__(self) -> None:
        missing = [v for v in self.REQUIRED_ENV_VARS if not os.getenv(v)]
        if missing:
            print(f"❌ 環境変数が不足しています: {', '.join(missing)}")
            sys.exit(1)

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.db = DatabaseManager(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        self.news_collector = SimpleNewsCollector()
        self.writer = GeminiWriter(self.gemini_api_key)
        self.poster = AutoPoster(
            os.getenv("BLOG_URL"), os.getenv("BLOG_USERNAME"), os.getenv("BLOG_PASSWORD")
        )
        self.max_content_length = int(os.getenv("MAX_CONTENT_LENGTH", 500))

        print("✅ システム初期化完了")

    def _select_best_article(self, articles: List[Dict]) -> Dict:
        recent = self.db.get_recent_posts(30)
        posted = {p["title"] for p in recent}
        for a in articles:
            if a["title"] not in posted:
                return a
        return articles[0] if articles else {}

    def run_full_automation(self) -> bool:
        print("\n🚀 完全自動投稿フロー開始")
        arts = self.news_collector.get_ai_news(limit=5)
        if not arts:
            print("❌ ニュース取得失敗")
            return False
        for art in arts:
            self.db.save_news_article(art)

        print("🎯 記事選定")
        target = self._select_best_article(arts)

        print("✍️ 原稿作成")
        post = self.writer.generate_blog_post(target, self.max_content_length)
        post_id = self.db.save_generated_post(post)
        if not post_id:
            print("❌ 原稿保存失敗")
            return False

        print("📝 ブログ投稿")
        if self.poster.post_article(post):
            url = self.poster.verify_post(post) or ""
            self.db.update_post_status(post_id, "published", url)
            print(f"🎉 投稿完了: {url}")
            return True
        else:
            self.db.update_post_status(post_id, "failed")
            print("❌ 投稿失敗")
            return False

    def show_dashboard(self) -> None:
        stats = self.db.get_system_stats()
        print("\n📊 ダッシュボード")
        for k, v in stats.items():
            print(f"{k:20}: {v}")

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py [auto|dashboard]")
        return
    cmd = sys.argv[1]
    system = AutoAIBlogSystem()
    if cmd == "auto":
        system.run_full_automation()
    else:
        system.show_dashboard()

if __name__ == "__main__":
    main()
