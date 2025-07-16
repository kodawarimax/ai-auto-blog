#!/usr/bin/env python3
"""
完全自動 AI 投稿システム ― エントリポイント

・Supabase でデータを管理
・Gemini（Google Generative AI）で本文生成
・ブログに自動投稿
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

# ──────────────────────────────
# プロジェクトルートをパスに追加
# ──────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ──────────────────────────────
# 外部ライブラリ
# ──────────────────────────────
from dotenv import load_dotenv

load_dotenv()  # .env を読み込んで環境変数を設定

# ──────────────────────────────
# 自作モジュール
# ──────────────────────────────
from database import DatabaseManager
from auto_poster import AutoPoster

# ──────────────────────────────
# 可 optional なモジュール
# ──────────────────────────────
try:
    from news_collector import SimpleNewsCollector      # ニュース取得
    from gemini_writer import GeminiWriter              # Gemini で文章生成
except ImportError:
    # フォールバック実装（最低限動くようにする）
    class SimpleNewsCollector:
        def get_ai_news(self, limit: int = 3) -> List[Dict]:
            return [{
                "title": "AI 技術の最新動向",
                "summary": "AI 技術が急速に発展しています。",
                "url": "https://example.com/ai-news",
                "source": "fallback",
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

# ════════════════════════════════════════════════════════════════════════
# メインシステムクラス
# ════════════════════════════════════════════════════════════════════════
class AutoAIBlogSystem:
    """完全自動 AI 投稿システムの中枢クラス"""

    REQUIRED_ENV_VARS = [
        "GEMINI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "BLOG_URL",
        "BLOG_USERNAME",
        "BLOG_PASSWORD",
    ]

    def __init__(self) -> None:
        if not self._check_config():
            sys.exit(1)

        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.blog_url = os.getenv("BLOG_URL")
        self.blog_username = os.getenv("BLOG_USERNAME")
        self.blog_password = os.getenv("BLOG_PASSWORD")
        self.max_content_length = int(os.getenv("MAX_CONTENT_LENGTH", 500))

        # モジュール初期化
        self.db = DatabaseManager(self.supabase_url, self.supabase_key)
        self.news_collector = SimpleNewsCollector()
        self.writer = GeminiWriter(self.gemini_api_key)
        self.poster = AutoPoster(self.blog_url, self.blog_username, self.blog_password)

        print("✅ システム初期化完了")

    # ──────────────────────────────
    # 内部ユーティリティ
    # ──────────────────────────────
    def _check_config(self) -> bool:
        missing = [v for v in self.REQUIRED_ENV_VARS if not os.getenv(v)]
        if missing:
            print(f"❌ 環境変数が不足しています: {', '.join(missing)}")
            return False
        return True

    def _select_best_article(self, articles: List[Dict]) -> Dict:
        """直近 30 件の投稿タイトルを除外して最初に合致したニュースを返す"""
        recent_posts = self.db.get_recent_posts(30)
        posted_titles = {p["title"] for p in recent_posts}

        for article in articles:
            if article["title"] not in posted_titles:
                return article
        return articles[0] if articles else {}

    # ──────────────────────────────
    # パブリックメソッド
    # ──────────────────────────────
    def run_full_automation(self) -> bool:
        """完全自動投稿フローを実行"""
        print("\n🚀 完全自動投稿フロー開始")

        # 1. ニュース収集
        print("📰 STEP 1: ニュース収集")
        articles = self.news_collector.get_ai_news(limit=5)
        if not articles:
            self.db.save_system_log("ERROR", "ニュース収集に失敗")
            print("❌ ニュースが取得できませんでした")
            return False

        for art in articles:
            self.db.save_news_article(art)

        # 2. 記事選定
        print("🎯 STEP 2: 記事選定")
        target = self._select_best_article(articles)
        print(f"選定記事: {target['title']}")

        # 3. Gemini で原稿作成
        print("✍️ STEP 3: 原稿作成")
        post = self.writer.generate_blog_post(target, self.max_content_length)
        post_id = self.db.save_generated_post(post)
        if not post_id:
            self.db.save_system_log("ERROR", "原稿保存に失敗")
            print("❌ 原稿保存に失敗しました")
            return False

        # 4. ブログ投稿
        print("📝 STEP 4: ブログ投稿")
        if self.poster.post_article(post):
            url = self.poster.verify_post(post) or ""
            self.db.update_post_status(post_id, "published", url)
            self.db.save_system_log("INFO", "投稿成功", {"post_id": post_id, "url": url})
            print(f"🎉 投稿完了: {url}")
            return True
        else:
            self.db.update_post_status(post_id, "failed")
            self.db.save_system_log("ERROR", "投稿失敗", {"post_id": post_id})
            print("❌ 投稿に失敗しました")
            return False

    def test_system(self) -> None:
        """各種 API の疎通確認"""
        print("🔍 システムテスト開始")
        ok_gemini = ok_supabase = False

        # Gemini
        try:
            art = {"title": "テスト", "summary": "Gemini API テスト", "url": ""}
            self.writer.generate_blog_post(art, 100)
            ok_gemini = True
            print("✅ Gemini API OK")
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")

        # Supabase
        try:
            self.db.get_system_stats()
            ok_supabase = True
            print("✅ Supabase OK")
        except Exception as e:
            print(f"❌ Supabase Error: {e}")

        self.db.save_system_log(
            "INFO", "システムテスト", {"gemini": ok_gemini, "supabase": ok_supabase}
        )
        print("🔍 システムテスト終了")

    def show_dashboard(self) -> None:
        """統計情報を表示"""
        stats = self.db.get_system_stats()
        print("\n📊 ダッシュボード")
        print("------------------------------")
        for k, v in stats.items():
            print(f"{k:20}: {v}")
        print("------------------------------")


# ════════════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════════════
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py [auto|test|dashboard]")
        return

    cmd = sys.argv[1]
    system = AutoAIBlogSystem()

    if cmd == "auto":
        system.run_full_automation()
    elif cmd == "test":
        system.test_system()
    elif cmd == "dashboard":
        system.show_dashboard()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
