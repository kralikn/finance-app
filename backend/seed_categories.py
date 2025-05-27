# seed_categories.py
from app.database.database import SessionLocal
from app.database.models import Category


def seed_default_categories():
    db = SessionLocal()

    # Ellenőrzés: vannak-e már kategóriák
    existing = db.query(Category).count()
    if existing > 0:
        print(f"Categories already exist ({existing}). Skipping seed.")
        return

    # Default kategóriák
    default_categories = [
        # Income categories
        {"name": "Munkabér", "type": "income"},
        {"name": "Kamat", "type": "income"},
        {"name": "Egyéb bevétel", "type": "income"},
        # Expense categories
        {"name": "Élelmiszer", "type": "expense"},
        {"name": "Lakhatás", "type": "expense"},
        {"name": "Közlekedés", "type": "expense"},
        {"name": "Szórakozás", "type": "expense"},
        {"name": "Egészségügy", "type": "expense"},
        {"name": "Egyéb kiadás", "type": "expense"},
        {"name": "Bankköltség", "type": "expense"},
    ]

    try:
        for cat_data in default_categories:
            category = Category(**cat_data)
            db.add(category)

        db.commit()
        print(f"✅ Created {len(default_categories)} default categories")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_default_categories()
