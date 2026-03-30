import os
from app import engine, SessionLocal, Recipe, Base
from dotenv import load_dotenv

def init_db():
    load_dotenv()
    print("Connecting to database...")
    
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # 初期データチェック
    if db.query(Recipe).count() == 0:
        print("Adding sample data...")
        sample = Recipe(
            title="テストレシピ",
            minutes=10,
            description="これは初期データです。正常に接続されています。"
        )
        db.add(sample)
        db.commit()
        print("Success!")
    else:
        print("Data already exists. Skipping.")
    db.close()

if __name__ == "__main__":
    init_db()