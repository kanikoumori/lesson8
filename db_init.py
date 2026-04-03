import os
from app import engine, SessionLocal, Recipe, Base
from dotenv import load_dotenv

def init_db():
    load_dotenv()
    print("Database connecting...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    # テストデータの投入
    if db.query(Recipe).count() == 0:
        test_recipe = Recipe(
            title="初期レシピ",
            minutes=5,
            description="DB接続テストに成功しました。"
        )
        db.add(test_recipe)
        db.commit()
        print("Success: Sample data added.")
    else:
        print("Check: Data already exists.")
    db.close()

if __name__ == "__main__":
    init_db()