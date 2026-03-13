# -*- coding: utf-8 -*-
import os
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from flask import Flask, request, redirect, url_for, render_template_string
from sqlalchemy import create_engine, String, Integer, Text, DateTime, CheckConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

load_dotenv()

def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url

DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None

class Base(DeclarativeBase):
    pass

class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (CheckConstraint("minutes >= 1"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    minutes: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

if engine:
    Base.metadata.create_all(engine)

app = Flask(__name__)

HTML = """
<h1>レシピ投稿</h1>
<form method="post">
タイトル<input name="title"><br>
分数<input name="minutes" type="number"><br>
説明<textarea name="description"></textarea><br>
<button>投稿</button>
</form>
<hr>
{% for r in recipes %}
<div>
<b>{{r.title}}</b> {{r.minutes}}分<br>
{{r.description}}
</div>
{% endfor %}
"""

@app.route("/", methods=["GET","POST"])
def index():
    if request.method=="POST" and engine:
        with Session(engine) as s:
            s.add(Recipe(
                title=request.form["title"],
                minutes=int(request.form["minutes"]),
                description=request.form["description"]
            ))
            s.commit()
        return redirect(url_for("index"))

    recipes=[]
    if engine:
        with Session(engine) as s:
            recipes=s.query(Recipe).order_by(Recipe.id.desc()).all()

    return render_template_string(HTML,recipes=recipes)

if __name__ == "__main__":
    port=int(os.environ.get("PORT",8000))
    app.run(host="0.0.0.0",port=port)