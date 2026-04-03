import os
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- データベース設定 ---
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- データモデル ---
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    minutes = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- 共通HTMLテンプレート（編集・一覧の両方で利用） ---
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>レシピ管理アプリ</title>
    <style>
        body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; color: #333; line-height: 1.6; }
        .error { color: #721c24; background: #f8d7da; padding: 10px; border-radius: 4px; margin-bottom: 1rem; }
        form { background: #f9f9f9; padding: 1.5rem; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 2rem; }
        .field { margin-bottom: 1rem; }
        label { display: block; font-weight: bold; margin-bottom: 0.3rem; }
        input, textarea { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .btn { display: inline-block; padding: 0.6rem 1.2rem; border-radius: 4px; text-decoration: none; cursor: pointer; border: none; font-size: 0.9rem; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .recipe-item { border: 1px solid #eee; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; position: relative; }
        .actions { margin-top: 10px; text-align: right; }
        .actions a, .actions button { margin-left: 10px; }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
"""

# --- メイン画面（一覧＆新規投稿） ---
INDEX_TEMPLATE = """
{% extends "layout" %}
{% block content %}
    <h1>🍳 レシピ投稿</h1>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    
    <form method="POST">
        <div class="field">
            <label>タイトル</label>
            <input type="text" name="title" required>
        </div>
        <div class="field">
            <label>所要分数</label>
            <input type="number" name="minutes" min="1" required>
        </div>
        <div class="field">
            <label>説明</label>
            <textarea name="description" rows="2"></textarea>
        </div>
        <button type="submit" class="btn btn-primary">レシピを保存する</button>
    </form>

    <h2>最新のレシピ</h2>
    {% for recipe in recipes %}
    <div class="recipe-item">
        <strong>{{ recipe.title }}</strong> ({{ recipe.minutes }}分)
        <p>{{ recipe.description if recipe.description else '説明なし' }}</p>
        <div class="actions">
            <a href="{{ url_for('edit', id=recipe.id) }}" class="btn btn-secondary">編集</a>
            <form action="{{ url_for('delete', id=recipe.id) }}" method="POST" style="display:inline; background:none; border:none; padding:0; margin:0;">
                <button type="submit" class="btn btn-danger" onclick="return confirm('本当に削除しますか？')">削除</button>
            </form>
        </div>
    </div>
    {% endfor %}
{% endblock %}
"""

# --- 編集画面 ---
EDIT_TEMPLATE = """
{% extends "layout" %}
{% block content %}
    <h1>📝 レシピを編集</h1>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    
    <form method="POST">
        <div class="field">
            <label>タイトル</label>
            <input type="text" name="title" value="{{ recipe.title }}" required>
        </div>
        <div class="field">
            <label>所要分数</label>
            <input type="number" name="minutes" value="{{ recipe.minutes }}" min="1" required>
        </div>
        <div class="field">
            <label>説明</label>
            <textarea name="description" rows="4">{{ recipe.description }}</textarea>
        </div>
        <button type="submit" class="btn btn-primary">更新する</button>
        <a href="{{ url_for('index') }}" class="btn btn-secondary" style="text-align:center; display:block; margin-top:10px;">キャンセル</a>
    </form>
{% endblock %}
"""

# --- ルート設定 ---

@app.route("/", methods=["GET", "POST"])
def index():
    db = SessionLocal()
    error = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        minutes = request.form.get("minutes")
        description = request.form.get("description", "").strip()
        
        if title and minutes:
            try:
                new_recipe = Recipe(title=title, minutes=int(minutes), description=description)
                db.add(new_recipe)
                db.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.rollback()
                error = f"保存エラー: {e}"
        else:
            error = "必須項目を入力してください。"

    recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).all()
    db.close()
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', INDEX_TEMPLATE), recipes=recipes, error=error)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = SessionLocal()
    recipe = db.query(Recipe).filter(Recipe.id == id).first()
    error = None

    if not recipe:
        db.close()
        return "レシピが見つかりません", 404

    if request.method == "POST":
        recipe.title = request.form.get("title", "").strip()
        recipe.minutes = int(request.form.get("minutes", 1))
        recipe.description = request.form.get("description", "").strip()
        
        try:
            db.commit()
            db.close()
            return redirect(url_for('index'))
        except Exception as e:
            db.rollback()
            error = f"更新エラー: {e}"

    # 編集用HTMLの描画
    content = render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', EDIT_TEMPLATE), recipe=recipe, error=error)
    db.close()
    return content

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    db = SessionLocal()
    recipe = db.query(Recipe).filter(Recipe.id == id).first()
    if recipe:
        try:
            db.delete(recipe)
            db.commit()
        except Exception as e:
            db.rollback()
    db.close()
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)