# 🤖 完全自動AI投稿システム

**GitHub Actions + Supabase で完全自動化！**

## ✨ 特徴

### 🚀 完全自動化
- **GitHub Actions** で毎日午前9時に自動実行
- **Supabase** データベースで状態管理
- **複数投稿方法** でフォールバック
- **完全なログ記録** と監視

### 🎯 シンプル設計
- **4つのライブラリ** のみ
- **2つのアカウント** のみ（Google AI + Supabase）
- **5分でセットアップ** 完了
- **メンテナンス不要**

### 🛡️ 高い信頼性
- **多段階フォールバック** 機能
- **自動リトライ** 機能
- **詳細な監視** とダッシュボード
- **エラー自動復旧**

## 📋 必要なもの

### アカウント（2個のみ）
1. **Google AI Studio** - Gemini API（無料）
2. **Supabase** - データベース（無料）

### ライブラリ（4個のみ）
```
google-generativeai  # Gemini AI
supabase            # データベース
requests            # HTTP通信
python-dotenv       # 設定管理
```

## 🚀 セットアップ（5分）

### 1. リポジトリ作成
```bash
# GitHubで新しいリポジトリを作成
# このZIPファイルの内容をアップロード
```

### 2. Supabaseプロジェクト作成
1. [Supabase](https://supabase.com) でアカウント作成
2. 新しいプロジェクトを作成
3. SQL Editorで以下を実行:

```sql
-- ニュース記事テーブル
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    summary TEXT,
    source TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 生成投稿テーブル
CREATE TABLE generated_posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    hashtags TEXT,
    source_url TEXT,
    generated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW(),
    status TEXT DEFAULT 'generated',
    blog_url TEXT
);

-- システムログテーブル
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. GitHub Secrets設定
GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定:

```
GEMINI_API_KEY=your-gemini-api-key
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key
BLOG_URL=https://uword-matching.com/um/miniblog/
BLOG_USERNAME=your-blog-username
BLOG_PASSWORD=your-blog-password
```

### 4. 自動実行開始
- GitHub Actions が毎日午前9時に自動実行
- 手動実行も可能（Actions タブから）

## 🎮 使い方

### 完全自動化（推奨）
```bash
# GitHub Actions が自動実行
# 何もする必要なし！
```

### 手動実行
```bash
# ローカルでテスト
python main.py test

# 1回だけ実行
python main.py auto

# ダッシュボード確認
python main.py dashboard

# 失敗投稿の再試行
python main.py retry
```

## 📊 監視・管理

### ダッシュボード
```bash
python main.py dashboard
```

出力例:
```
📊 システムダッシュボード
==================================================
📈 総記事数: 45
📝 総投稿数: 42
✅ 公開済み: 40
📅 今日の投稿: 1
🎯 成功率: 95.2%

📝 最近の投稿 (5件):
  1. ✅ Google Gemini AIの新機能が発表
  2. ✅ ChatGPT-5の開発が進行中
  3. ✅ AI画像生成技術の最新動向
  4. ✅ 自動運転技術の進歩
  5. ✅ 量子コンピューターとAIの融合
==================================================
```

### Supabaseダッシュボード
- リアルタイムでデータ確認
- SQL クエリで詳細分析
- 自動バックアップ

## 🔧 カスタマイズ

### 投稿時間変更
`.github/workflows/auto-post.yml` の cron を編集:
```yaml
# 毎日午後6時（UTC 9時）に変更
- cron: '0 9 * * *'
```

### 文字数制限変更
GitHub Secrets で `MAX_CONTENT_LENGTH` を設定

### 投稿頻度変更
```yaml
# 週3回（月・水・金）
- cron: '0 0 * * 1,3,5'

# 毎時間
- cron: '0 * * * *'
```

## 🛡️ エラー対応

### 自動復旧機能
1. **投稿失敗時**: 自動的に別の方法で再試行
2. **API制限時**: 次回実行時に自動リトライ
3. **ネットワークエラー**: 指数バックオフで再試行

### 手動復旧
```bash
# 失敗した投稿を再試行
python main.py retry

# システム状態確認
python main.py test
```

### ログ確認
- **GitHub Actions**: Actions タブでログ確認
- **Supabase**: system_logs テーブルで詳細確認

## 📈 システム構成

```
GitHub Actions (無料)
    ↓ 毎日午前9時実行
Python アプリケーション
    ↓ ニュース収集
RSS/Web スクレイピング
    ↓ AI記事生成
Gemini AI (無料)
    ↓ 投稿実行
ブログサイト
    ↓ 状態記録
Supabase (無料)
```

## 💰 運用コスト

### 完全無料運用
- **GitHub Actions**: 月2000分無料（十分）
- **Supabase**: 500MB無料（十分）
- **Gemini AI**: 無料枠あり
- **合計**: 月額0円

### 大量使用時
- **Gemini AI**: 月$1-5程度
- **Supabase**: 月$25（大量データ時）

## 🎯 成功事例

### 典型的な1日の流れ
```
09:00 - GitHub Actions 自動実行開始
09:01 - ニュース収集完了（5件）
09:02 - AI記事生成完了
09:03 - ブログ投稿成功
09:04 - Supabase に結果記録
09:05 - 処理完了、次回まで待機
```

### 月間実績例
- **投稿数**: 30件
- **成功率**: 96.7%
- **平均処理時間**: 3分
- **エラー**: 1件（自動復旧済み）

## 🔄 アップグレード

### 機能拡張
- 複数ブログサイト対応
- SNS連携投稿
- 画像自動生成・添付
- 記事品質スコアリング

### 高度な監視
- Slack/Discord 通知
- メール レポート
- 詳細分析ダッシュボード

## 🆘 サポート

### よくある問題

#### ❌ GitHub Actions が実行されない
```
解決方法:
1. リポジトリが public であることを確認
2. .github/workflows/auto-post.yml が正しい場所にあることを確認
3. GitHub Secrets が正しく設定されていることを確認
```

#### ❌ Supabase 接続エラー
```
解決方法:
1. プロジェクトURLとAPIキーを再確認
2. テーブルが正しく作成されていることを確認
3. RLS（Row Level Security）が無効になっていることを確認
```

#### ❌ ブログ投稿失敗
```
解決方法:
1. ログイン情報を再確認
2. ブログサイトの仕様変更を確認
3. 手動でログインできることを確認
```

### 学習リソース
- [GitHub Actions ドキュメント](https://docs.github.com/actions)
- [Supabase ドキュメント](https://supabase.com/docs)
- [Gemini AI ドキュメント](https://ai.google.dev/docs)

---

**🎊 これで完全自動化の完成です！**

一度セットアップすれば、毎日自動でAIニュースブログが投稿され続けます。
メンテナンス不要で、高い信頼性を持つシステムをお楽しみください！

