レシピ投稿ミニアプリ (Flask + Render PostgreSQL)
FlaskとSQLAlchemyを使用した、最小構成のレシピ管理アプリです。

🚀 Render セットアップ手順
GitHubへリポジトリを作成し、全ファイルをプッシュします。

PostgreSQLの作成:

Render Dashboardで「New → PostgreSQL」を選択。

インスタンスタイプは Free を選択。

作成後、Internal Database URL をコピーしておきます。

Web Serviceの作成:

「New → Web Service」を選択し、リポジトリを連携。

Runtime: Python

Build Command: pip install -r requirements.txt

Start Command: python app.py

環境変数の設定 (Environment Variables):

DATABASE_URL: コピーした Internal Database URL を貼り付け。

DEBUG: false

デプロイ: 公開URLにアクセスし、投稿ができるか確認してください