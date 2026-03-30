import os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for
from sqlalchemy import create_all, create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# .envファイルがあれば読み込む（ローカル開発用）
load_dotenv()

app = Flask(__name__)

# --- データベース設定 ---
database_url = os.environ.get("DATABASE_URL")
# Renderのpostgres:// を SQLAlchemy用の postgresql+psycopg2:// に置換
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)

# データベース接続エンジンの作成（pool_pre_pingで接続断切れ対策）
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- モデル定義 ---
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    minutes = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 起動時にテーブルを作成
Base.metadata.create_all(bind=engine)

# --- HTMLテンプレート (1ファイル構成用) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>レシピ投稿ミニアプリ</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 20px auto; padding: 0 10px; line-height: 1.6; }
        .error { color: red; background: #fee; padding: 10px; border-radius: 5px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; }
        input[type="text"], input[type="number"], textarea { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; }
        .recipe-card { border-bottom: 1px solid #ddd; padding: 10px 0; }
        .recipe-meta { font-size: 0.8em; color: #666; }
    </style>
</head>
<body>
    <h1>🍳 レシピ投稿</h1>

    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}

    <form method="POST" action="/">
        <div class="form-group">
            <label>タイトル (必須)</label>
            <input type="text" name="title" value="{{ request.form.get('title', '') }}" placeholder="例: 肉じゃが">
        </div>
        <div class="form-group">
            <label>所要分数 (必須・数値)</label>
            <input type="number" name="minutes" value="{{ request.form.get('minutes', '') }}" min="1" placeholder="30">
        </div>
        <div class="form-group">
            <label>説明</label>
            <textarea name="description" rows="3">{{ request.form.get('description', '') }}</textarea>
        </div>
        <button type="submit">レシピを投稿する</button>
    </form>

    <hr>

    <h2>最新のレシピ一覧</h2>
    {% for recipe in recipes %}
    <div class="recipe-card">
        <strong>{{ recipe.title }}</strong> ({{ recipe.minutes }}分)
        <p>{{ recipe.description if recipe.description else '説明なし' }}</p>
        <div class="recipe-meta">投稿日: {{ recipe.created_at.strftime('%Y-%m-%d %H:%M') }} (UTC)</div>
    </div>
    {% else %}
    <p>まだ投稿がありません。</p>
    {% endfor %}
</body>
</html>
"""

# --- ルートハンドラ ---
@app.route("/", methods=["GET", "POST"])
def index():
    db = SessionLocal()
    error = None

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        minutes_raw = request.form.get("minutes", "")
        description = request.form.get("description", "").strip()

        # シンプルなバリデーション
        if not title:
            error = "タイトルを入力してください。"
        elif not minutes_raw.isdigit() or int(minutes_raw) < 1:
            error = "所要分数は1以上の数値を入力してください。"
        
        if not error:
            try:
                new_recipe = Recipe(title=title, minutes=int(minutes_raw), description=description)
                db.add(new_recipe)
                db.commit()
                return redirect(url_for("index")) # PRGパターン
            except Exception as e:
                db.rollback()
                error = f"保存エラーが発生しました: {str(e)}"
    
    # 新しい順に取得
    recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).all()
    db.close()
    
    return render_template_string(HTML_TEMPLATE, recipes=recipes, error=error)

if __name__ == "__main__":
    # Renderの環境変数PORTに対応。デフォルトは8000
    port = int(os.environ.get("PORT", 8000))
    # 環境変数DEBUGが "true" (小文字) の場合のみデバッグモードON
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)