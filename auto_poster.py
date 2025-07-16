"""
完全自動AI投稿システム - 自動投稿モジュール

"""
+import os
+from dotenv import load_dotenv
+load_dotenv()
import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, Optional
from datetime import datetime
import json

class AutoPoster:
    """完全自動投稿クラス"""
    
    def __init__(self, blog_url: str, username: str, password: str):
        self.blog_url = blog_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.is_logged_in = False
    
    def login(self) -> bool:
        """ブログにログイン"""
        if self.is_logged_in:
            return True
            
        try:
            print("🔐 ブログにログイン中...")
            
            # ログインページを取得
            login_url = f"{self.blog_url}/"
            response = self.session.get(login_url, timeout=30)
            response.raise_for_status()
            
            # ログインフォームを解析
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 複数のログイン方法を試行
            login_success = False
            
            # 方法1: 標準的なログインフォーム
            login_form = soup.find('form')
            if login_form and not login_success:
                login_success = self._try_standard_login(login_form)
            
            # 方法2: AJAX ログイン
            if not login_success:
                login_success = self._try_ajax_login()
            
            # 方法3: API ログイン
            if not login_success:
                login_success = self._try_api_login()
            
            if login_success:
                self.is_logged_in = True
                print("✅ ログインに成功しました")
                return True
            else:
                print("❌ すべてのログイン方法が失敗しました")
                return False
                
        except Exception as e:
            print(f"❌ ログインエラー: {e}")
            return False
    
    def _try_standard_login(self, login_form) -> bool:
        """標準的なフォームログインを試行"""
        try:
            # フォームデータを準備
            form_data = {}
            for input_tag in login_form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value
            
            # ユーザー名とパスワードを設定
            form_data['username'] = self.username
            form_data['password'] = self.password
            
            # ログイン実行
            action = login_form.get('action', '')
            if action.startswith('/'):
                login_post_url = f"{self.blog_url}{action}"
            else:
                login_post_url = f"{self.blog_url}/{action}"
            
            response = self.session.post(login_post_url, data=form_data, timeout=30)
            
            # ログイン成功確認
            return "ログイン" not in response.text and response.status_code == 200
            
        except Exception as e:
            print(f"標準ログイン失敗: {e}")
            return False
    
    def _try_ajax_login(self) -> bool:
        """AJAXログインを試行"""
        try:
            login_data = {
                'username': self.username,
                'password': self.password,
                'action': 'login'
            }
            
            ajax_url = f"{self.blog_url}/ajax/login"
            response = self.session.post(ajax_url, json=login_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            
            return False
            
        except Exception as e:
            print(f"AJAXログイン失敗: {e}")
            return False
    
    def _try_api_login(self) -> bool:
        """APIログインを試行"""
        try:
            api_data = {
                'user': self.username,
                'pass': self.password
            }
            
            api_url = f"{self.blog_url}/api/auth"
            response = self.session.post(api_url, data=api_data, timeout=30)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"APIログイン失敗: {e}")
            return False
    
    def post_article(self, blog_post: Dict) -> bool:
        """記事を投稿"""
        if not self.login():
            return False
        
        try:
            print(f"📝 記事を投稿中: {blog_post['title']}")
            
            # 複数の投稿方法を試行
            post_success = False
            
            # 方法1: 標準的なフォーム投稿
            post_success = self._try_form_post(blog_post)
            
            # 方法2: AJAX投稿
            if not post_success:
                post_success = self._try_ajax_post(blog_post)
            
            # 方法3: API投稿
            if not post_success:
                post_success = self._try_api_post(blog_post)
            
            if post_success:
                print("✅ 記事の投稿が完了しました")
                return True
            else:
                print("❌ すべての投稿方法が失敗しました")
                return False
                
        except Exception as e:
            print(f"❌ 投稿エラー: {e}")
            return False
    
    def _try_form_post(self, blog_post: Dict) -> bool:
        """フォーム投稿を試行"""
        try:
            # 新規投稿ページを取得
            new_post_url = f"{self.blog_url}/"
            response = self.session.get(new_post_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 投稿フォームを探す
            post_form = soup.find('form')
            if not post_form:
                return False
            
            # フォームデータを準備
            form_data = {}
            for input_tag in post_form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value
            
            # 記事内容を設定
            full_content = f"{blog_post['title']}\n\n{blog_post['content']}"
            if len(full_content) > 500:
                full_content = full_content[:497] + "..."
            
            # テキストエリアの名前を推測
            textarea = post_form.find('textarea')
            textarea_name = textarea.get('name', 'content') if textarea else 'content'
            form_data[textarea_name] = full_content
            
            # ハッシュタグを設定
            if 'hashtags' in blog_post:
                form_data['hashtags'] = blog_post['hashtags']
                form_data['tags'] = blog_post['hashtags']
            
            # 投稿実行
            action = post_form.get('action', '')
            if action.startswith('/'):
                post_url = f"{self.blog_url}{action}"
            else:
                post_url = f"{self.blog_url}/{action}"
            
            response = self.session.post(post_url, data=form_data, timeout=30)
            return response.status_code == 200
            
        except Exception as e:
            print(f"フォーム投稿失敗: {e}")
            return False
    
    def _try_ajax_post(self, blog_post: Dict) -> bool:
        """AJAX投稿を試行"""
        try:
            full_content = f"{blog_post['title']}\n\n{blog_post['content']}"
            if len(full_content) > 500:
                full_content = full_content[:497] + "..."
            
            post_data = {
                'title': blog_post['title'],
                'content': full_content,
                'hashtags': blog_post.get('hashtags', ''),
                'action': 'create_post'
            }
            
            ajax_url = f"{self.blog_url}/ajax/post"
            response = self.session.post(ajax_url, json=post_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            
            return False
            
        except Exception as e:
            print(f"AJAX投稿失敗: {e}")
            return False
    
    def _try_api_post(self, blog_post: Dict) -> bool:
        """API投稿を試行"""
        try:
            full_content = f"{blog_post['title']}\n\n{blog_post['content']}"
            if len(full_content) > 500:
                full_content = full_content[:497] + "..."
            
            api_data = {
                'post_title': blog_post['title'],
                'post_content': full_content,
                'post_tags': blog_post.get('hashtags', '')
            }
            
            api_url = f"{self.blog_url}/api/posts"
            response = self.session.post(api_url, data=api_data, timeout=30)
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            print(f"API投稿失敗: {e}")
            return False
    
    def verify_post(self, blog_post: Dict) -> Optional[str]:
        """投稿が成功したかを確認し、URLを返す"""
        try:
            # ブログのトップページを確認
            response = self.session.get(f"{self.blog_url}/", timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 投稿タイトルを含むリンクを探す
                title_keywords = blog_post['title'][:20]
                for link in soup.find_all('a'):
                    if link.get_text() and title_keywords in link.get_text():
                        href = link.get('href', '')
                        if href.startswith('/'):
                            return f"{self.blog_url}{href}"
                        elif href.startswith('http'):
                            return href
            
            return None
            
        except Exception as e:
            print(f"投稿確認エラー: {e}")
            return None

if __name__ == "__main__":
    # テスト実行
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    blog_url = os.getenv('BLOG_URL')
    username = os.getenv('BLOG_USERNAME')
    password = os.getenv('BLOG_PASSWORD')
    
    if not all([blog_url, username, password]):
        print("❌ ブログ設定が不完全です")
        exit(1)
    
    poster = AutoPoster(blog_url, username, password)
    
    # テスト用投稿
    test_post = {
        'title': 'AI技術の最新動向',
        'content': 'AI技術が急速に発展しています。特に自然言語処理の分野では、ChatGPTやGeminiなどの大規模言語モデルが注目を集めています。これらの技術により、私たちの生活がより便利になることが期待されています。',
        'hashtags': '#AI #人工知能 #テクノロジー'
    }
    
    success = poster.post_article(test_post)
    
    if success:
        # 投稿確認
        post_url = poster.verify_post(test_post)
        if post_url:
            print(f"✅ 投稿確認成功: {post_url}")
        else:
            print("⚠️ 投稿確認できませんでした")
    
    print(f"投稿結果: {'成功' if success else '失敗'}")

