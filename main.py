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

class AutoAIBlogSystem:
    """完全自動AI投稿システムのメインクラス"""
    
    def __init__(self):
        # 環境変数を読み込み
        load_dotenv()
        
        # 設定を取得
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.blog_url = os.getenv('BLOG_URL')
        self.blog_username = os.getenv('BLOG_USERNAME')
        self.blog_password = os.getenv('BLOG_PASSWORD')
        self.max_content_length = int(os.getenv('MAX_CONTENT_LENGTH', 500))
        
        # 設定チェック
        if not self._check_config():
            print("❌ 設定が不完全です。環境変数を確認してください。")
            sys.exit(1)
        
        # モジュールを初期化
        try:
            self.db = DatabaseManager(self.supabase_url, self.supabase_key)
            self.news_collector = SimpleNewsCollector()
            self.writer = GeminiWriter(self.gemini_api_key)
            self.poster = AutoPoster(self.blog_url, self.blog_username, self.blog_password)
            print("✅ 完全自動AI投稿システムを初期化しました")
        except Exception as e:
            print(f"❌ システム初期化エラー: {e}")
            sys.exit(1)
    
    def _check_config(self) -> bool:
        """設定の完全性をチェック"""
        required_vars = [
            'GEMINI_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'BLOG_URL',
            'BLOG_USERNAME',
            'BLOG_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def run_full_automation(self):
        """完全自動化処理を実行"""
        print(f"\n🚀 完全自動化処理を開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # システムログ記録開始
            self.db.save_system_log('INFO', '自動化処理開始')
            
            # 1. ニュース収集
            print("\n📰 STEP 1: ニュース収集")
            news_articles = self.news_collector.get_ai_news(limit=5)
            
            if not news_articles:
                self.db.save_system_log('ERROR', 'ニュース収集失敗')
                print("❌ ニュースが取得できませんでした")
                return False
            
            # ニュースをデータベースに保存
            for article in news_articles:
                self.db.save_news_article(article)
            
            print(f"✅ {len(news_articles)}件のニュースを収集・保存しました")
            
            # 2. 最適な記事を選択
            print("\n🎯 STEP 2: 記事選択")
            selected_article = self._select_best_article(news_articles)
            print(f"選択された記事: {selected_article['title']}")
            
            # 3. Gemini AIでブログ記事生成
            print("\n✍️ STEP 3: ブログ記事生成")
            blog_post = self.writer.generate_blog_post(selected_article, self.max_content_length)
            
            # 生成された投稿をデータベースに保存
            post_id = self.db.save_generated_post(blog_post)
            
            if not post_id:
                self.db.save_system_log('ERROR', '投稿保存失敗')
                print("❌ 生成された投稿の保存に失敗しました")
                return False
            
            print(f"✅ ブログ記事を生成・保存しました (ID: {post_id})")
            
            # 4. ブログに自動投稿
            print("\n📝 STEP 4: ブログ自動投稿")
            success = self.poster.post_article(blog_post)
            
            if success:
                # 投稿成功の確認
                post_url = self.poster.verify_post(blog_post)
                
                # データベースのステータス更新
                self.db.update_post_status(post_id, 'published', post_url)
                
                # 成功ログ記録
                self.db.save_system_log('INFO', '投稿成功', {
                    'post_id': post_id,
                    'title': blog_post['title'],
                    'url': post_url
                })
                
                print("🎉 完全自動投稿が成功しました！")
                if post_url:
                    print(f"📍 投稿URL: {post_url}")
                
                return True
            else:
                # 投稿失敗の記録
                self.db.update_post_status(post_id, 'failed')
                self.db.save_system_log('ERROR', '投稿失敗', {
                    'post_id': post_id,
                    'title': blog_post['title']
                })
                
                print("❌ 自動投稿に失敗しました")
                return False
                
        except Exception as e:
            error_msg = f"自動化処理エラー: {e}"
            print(f"❌ {error_msg}")
            self.db.save_system_log('ERROR', error_msg)
            return False
    
    def _select_best_article(self, articles: list) -> dict:
        """最も投稿に適した記事を選択"""
        # 既に投稿済みの記事を除外
        recent_posts = self.db.get_recent_posts(30)
        posted_titles = [post['title'] for post in recent_posts]
        
        for article in articles:
            if article['title'] not in posted_titles:
                return article
        
        # すべて投稿済みの場合は最初の記事を返す
        return articles[0] if articles else {}
    
    def test_system(self):
        """システムテスト"""
        print("🔍 システムテストを実行中...")
        
        test_results = {}
        
        # Gemini API テスト
        try:
            test_article = {
                'title': 'テスト記事',
                'summary': 'これはテスト用の記事です。',
                'url': 'https://example.com'
            }
            
            self.writer.generate_blog_post(test_article, 100)
            test_results['gemini_api'] = True
            print("✅ Gemini API: 接続成功")
        except Exception as e:
            test_results['gemini_api'] = False
            print(f"❌ Gemini API: 接続失敗 - {e}")
        
        # Supabase テスト
        try:
            stats = self.db.get_system_stats()
            test_results['supabase'] = True
            print("✅ Supabase: 接続成功")
        except Exception as e:
            test_results['supabase'] = False
            print(f"❌ Supabase: 接続失敗 - {e}")
        
        # テスト結果をデータベースに記録
        self.db.save_system_log('INFO', 'システムテスト実行', test_results)
        
        print("🔍 システムテスト完了")
        return all(test_results.values())
    
    def show_dashboard(self):
        """システムダッシュボードを表示"""
        print("\n📊 システムダッシュボード")
        print("=" * 50)
        
        # システム統計
        stats = self.db.get_system_stats()
        print(f"📈 総記事数: {stats.get('total_articles', 0)}")
        print(f"📝 総投稿数: {stats.get('total_posts', 0)}")
        print(f"✅ 公開済み: {stats.get('published_posts', 0)}")
        print(f"📅 今日の投稿: {stats.get('today_posts', 0)}")
        print(f"🎯 成功率: {stats.get('success_rate', 0)}%")
        
        print("=" * 50)


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print(" python main.py [コマンド]")
        print("")
        print("利用可能なコマンド:")
        print(" auto - 完全自動化実行")
        print(" test - システムテスト")
        print(" dashboard - ダッシュボード表示")
        return
    
    command = sys.argv[1]
    
    try:
        system = AutoAIBlogSystem()
        
        if command == "auto":
            system.run_full_automation()
        elif command == "test":
            system.test_system()
        elif command == "dashboard":
            system.show_dashboard()
        else:
            print(f"❌ 不明なコマンド: {command}")
            
    except Exception as e:
        print(f"❌ システムエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
