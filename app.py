import os
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- データベース設定 (psycopg3対応) ---
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url and database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    minutes = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

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
    
    recipes = db.query(Recipe).order_by(Recipe.created_at.desc()).all()
    db.close()
    # render_template を使い、HTMLファイルを指定する
    return render_template("index.html", recipes=recipes, error=error)

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

    # edit.html を読み込む
    content = render_template("edit.html", recipe=recipe, error=error)
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
    app.run(host="0.0.0.0", port=port, debug=True)