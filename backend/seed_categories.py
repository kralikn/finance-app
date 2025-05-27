# seed_categories.py
from app.database.database import SessionLocal
from app.database.models import Category, CategoryKeyword


def seed_default_categories():
    db = SessionLocal()

    try:
        # Ellenőrzés: vannak-e már kategóriák
        existing = db.query(Category).count()
        if existing > 0:
            print(f"Categories already exist ({existing}). Skipping seed.")
            return

        # Default kategóriák kulcsszavakkal
        categories_data = [
            # Income categories
            {
                "name": "Munkabér",
                "type": "income",
                "keywords": [
                    "BPION",
                ],
            },
            {
                "name": "Kamat",
                "type": "income",
                "keywords": ["KAMATJÓVÁÍRÁS"],
            },
            {
                "name": "Egyéb bevétel",
                "type": "income",
                "keywords": ["MOHU"],
            },
            # Expense categories
            {
                "name": "Élelmiszer",
                "type": "expense",
                "keywords": ["TESCO", "LIDL", "AUCHAN", "SPAR"],
            },
            {
                "name": "Lakhatás",
                "type": "expense",
                "keywords": [],
            },
            {
                "name": "Közlekedés",
                "type": "expense",
                "keywords": ["BKK", "VOLÁN", "MÁV"],
            },
            {
                "name": "Szórakozás",
                "type": "expense",
                "keywords": ["NETFLIX"],
            },
            {
                "name": "Egészségügy",
                "type": "expense",
                "keywords": [],
            },
            {
                "name": "Képzés",
                "type": "expense",
                "keywords": ["UDEMY"],
            },
            {
                "name": "Bankköltség",
                "type": "expense",
                "keywords": [
                    "HAVI CSOMAGDÍJ",
                    "IDŐSZAKOS KÖLTSÉGEK",
                ],
            },
            {
                "name": "Egyéb kiadás",
                "type": "expense",
                "keywords": [],
            },
        ]

        # Kategóriák létrehozása kulcsszavakkal
        for cat_data in categories_data:
            keywords_list = cat_data.pop("keywords", [])

            # Kategória létrehozása
            category = Category(**cat_data)

            # Kulcsszavak hozzáadása
            for keyword in keywords_list:
                category_keyword = CategoryKeyword(keyword=keyword)
                category.keywords.append(category_keyword)

            db.add(category)

        db.commit()
        print(f"✅ Created {len(categories_data)} categories with keywords")

        # Ellenőrzés - létrehozott kategóriák és kulcsszavak listázása
        categories = db.query(Category).order_by(Category.type, Category.name).all()
        print("\n📋 Created categories with keywords:")

        current_type = None
        for cat in categories:
            if cat.type != current_type:
                print(f"\n{cat.type.upper()}:")
                current_type = cat.type

            keywords = [kw.keyword for kw in cat.keywords]
            print(f"  - {cat.name}: {keywords}")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_default_categories()
