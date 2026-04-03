import os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む（ローカル開発用）
load_dotenv()

app = Flask(__name__)

# --- データベース設定 ---
# Renderが提供する postgres:// を SQLAlchemy用の postgresql+psycopg:// に置換
# ※Python 3.13/3.14環境向けに最新の psycopg ドライバを使用します
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# データベース接続エンジンの作成
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- データモデル定義 ---
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    minutes = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 起動時にテーブルを自動作成
Base.metadata.create_all(bind=engine)

# --- 画面デザイン (HTML/CSS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>レシピ投稿アプリ</title>
    <style>
        body { font-family: "Helvetica Neue", Arial, sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; color: #333; }
        .error { color: #721c24; background-color: #f8d7da; padding: 10px; border-radius: 4px; margin-bottom: 1rem; }
        form { background: #f9f9f9; padding: 1.5rem; border-radius: 8px; border: 1px solid #ddd; }
        .field { margin-bottom: 1rem; }
        label { display: block; font-weight: bold; margin-bottom: 0.5rem; }
        input, textarea { width: 100%; padding: 0.5rem; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #007bff; color: white; border: none; padding: 0.7rem 1.5rem; border-radius: 4px; cursor: pointer; width: 100%; font-size: 1rem; }
        button:hover { background: #0056b3; }
        .recipe-list { margin-top: 2rem; }
        .recipe-item { border-bottom: 1px solid #eee; padding: 1rem 0; }
        .recipe-item:last-child { border: none; }
        .time { color: #666; font-size: 0.9rem; }
    </style>
</head>
<body>
    <h1>🍳 レシピ投稿</h1>

    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}

    <form method="POST">
        <div class="field">
            <label>タイトル (必須)</label>
            <input type="text" name="title" required placeholder="例: 簡単肉じゃが">
        </div>
        <div class="field">
            <label>所要分数 (必須・1分以上)</label>
            <input type="number" name="minutes" min="1" required placeholder="30">
        </div>
        <div class="field">
            <label>説明 (任意)</label>
            <textarea name="description" rows="3"></textarea>
        </div>
        <button type="submit">レシピを保存する</button>
    </form>

    <div class="recipe-list">
        <h2>最新のレシピ</h2>
        {% for recipe in recipes %}
        <div class="recipe-item">
            <strong>{{ recipe.title }}</strong> <span class="time">({{ recipe.minutes }}分)</span>
            <p>{{ recipe.description if recipe.description else '説明はありません' }}</p>
        </div>
        {% else %}
        <p>登録されたレシピはまだありません。</p>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    db = SessionLocal()
    error = None
    if request.method == "POST":
        title = request.form.get("title")
        minutes = request.form.get("minutes")
        description = request.form.get("description")

        # バリデーション
        if not title:
            error = "タイトルは必須です。"
        elif not minutes or not minutes.isdigit() or int(minutes) < 1:
            error = "所要分数は1以上の数値を入力してください。"
        
        if not error:
            try:
                new_recipe = Recipe(title=title, minutes=int(minutes), description=description)
                db.add(new_recipe)
                db.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.rollback()
                error = f"保存中にエラーが発生しました: {e}"

    recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).all()
    db.close()
    return render_template_string(HTML_TEMPLATE, recipes=recipes, error=error)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)