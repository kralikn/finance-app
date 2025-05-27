# test_encoding_direct.py
from app.database.database import SessionLocal
from app.database.models import Category, CategoryKeyword


def test_direct_insert():
    db = SessionLocal()

    try:
        print("=== PYTHON ENCODING TESZT ===")

        # Test string
        test_keyword = "IDŐSZAKOS KÖLTSÉGEK"
        print(f"Original keyword: {test_keyword}")
        print(f"Keyword type: {type(test_keyword)}")
        print(f"Keyword length: {len(test_keyword)}")
        print(f"Keyword bytes: {test_keyword.encode('utf-8')}")

        # Kategória létrehozása
        category = Category(name="Direct Test", type="expense")

        # Keyword objektum létrehozása
        keyword_obj = CategoryKeyword(keyword=test_keyword)
        print(f"CategoryKeyword.keyword before append: {keyword_obj.keyword}")

        category.keywords.append(keyword_obj)

        # Database mentés
        db.add(category)
        db.commit()
        db.refresh(category)

        # Ellenőrzés
        print(f"Saved keyword: {category.keywords[0].keyword}")
        print(f"Saved keyword type: {type(category.keywords[0].keyword)}")

        # Direct SQL query
        from sqlalchemy import text

        result = db.execute(
            text(
                "SELECT keyword FROM category_keywords WHERE keyword LIKE '%IDŐSZAKOS%' OR keyword LIKE '%IDOSZAKOS%'"
            )
        )
        rows = result.fetchall()
        print(f"Direct SQL result: {rows}")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_direct_insert()
