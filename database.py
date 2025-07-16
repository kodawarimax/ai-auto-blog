#!/usr/bin/env python3
"""
完全自動 AI 投稿システム ― Supabase データベース管理
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────
# Supabase クライアントの読み込み
# ──────────────────────────────
try:
    from supabase import Client, create_client  # type: ignore
except ImportError:
    # ランタイムに supabase-py が入っていない場合の簡易フォールバック
    Client = object  # type: ignore

    def create_client(url: str, key: str) -> Client:  # type: ignore
        raise RuntimeError("supabase-py がインストールされていません")


class DatabaseManager:
    """Supabase のデータ操作をラップするクラス"""

    # ──────────────────────────────
    # 初期化
    # ──────────────────────────────
    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        except Exception as e:
            print(f"❌ Supabase クライアント初期化失敗: {e}")
            raise

    # ──────────────────────────────
    # CRUD 操作
    # ──────────────────────────────
    def save_news_article(self, article: Dict) -> bool:
        data = {
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "summary": article.get("summary", ""),
            "source": article.get("source", ""),
            "published_at": article.get("published_at", datetime.utcnow().isoformat()),
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            res = (
                self.supabase.table("news_articles")  # type: ignore
                .insert(data)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            print(f"ニュース保存エラー: {e}")
            return False

    def save_generated_post(self, post: Dict) -> Optional[int]:
        data = {
            "title": post.get("title", ""),
            "content": post.get("content", ""),
            "hashtags": post.get("hashtags", ""),
            "source_url": post.get("source_url", ""),
            "generated_at": post.get("generated_at", datetime.utcnow().isoformat()),
            "status": "generated",
        }
        try:
            res = (
                self.supabase.table("generated_posts")  # type: ignore
                .insert(data)
                .execute()
            )
            return res.data[0]["id"] if res.data else None
        except Exception as e:
            print(f"投稿保存エラー: {e}")
            return None

    def update_post_status(
        self, post_id: int, status: str, blog_url: str | None = None
    ) -> bool:
        update_data: Dict[str, str] = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if blog_url:
            update_data["blog_url"] = blog_url
        if status == "published":
            update_data["published_at"] = datetime.utcnow().isoformat()
        try:
            res = (
                self.supabase.table("generated_posts")  # type: ignore
                .update(update_data)
                .eq("id", post_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            print(f"ステータス更新エラー: {e}")
            return False

    # ──────────────────────────────
    # 取得系
    # ──────────────────────────────
    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        try:
            res = (
                self.supabase.table("generated_posts")  # type: ignore
                .select("*")
                .order("generated_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data
        except Exception as e:
            print(f"投稿取得エラー: {e}")
            return []

    def get_system_stats(self) -> Dict:
        try:
            total_articles = (
                self.supabase.table("news_articles")  # type: ignore
                .select("id", count="exact")
                .execute()
            )
            total_posts = (
                self.supabase.table("generated_posts")  # type: ignore
                .select("id", count="exact")
                .execute()
            )
            published_posts = (
                self.supabase.table("generated_posts")  # type: ignore
                .select("id", count="exact")
                .eq("status", "published")
                .execute()
            )
            today = datetime.utcnow().date().isoformat()
            today_posts = (
                self.supabase.table("generated_posts")  # type: ignore
                .select("id", count="exact")
                .gte("published_at", today)
                .execute()
            )

            success_rate = (
                round((published_posts.count / max(total_posts.count, 1)) * 100, 2)
                if total_posts.count
                else 0
            )

            return {
                "total_articles": total_articles.count,
                "total_posts": total_posts.count,
                "published_posts": published_posts.count,
                "today_posts": today_posts.count,
                "success_rate": success_rate,
            }
        except Exception as e:
            print(f"統計取得エラー: {e}")
            return {}

    # ──────────────────────────────
    # システムログ
    # ──────────────────────────────
    def save_system_log(
        self, level: str, message: str, details: Dict | None = None
    ) -> None:
        data = {
            "level": level,
            "message": message,
            "details": json.dumps(details) if details else None,
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            self.supabase.table("system_logs").insert(data).execute()  # type: ignore
        except Exception as e:
            print(f"ログ保存エラー: {e}")
