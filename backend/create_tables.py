# create_tables.py
from app.database.database import engine, Base
from app.database.models import Category, Transaction

try:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

    # Ellenőrzés
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
            )
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"Created tables: {tables}")

except Exception as e:
    print(f"❌ Table creation failed: {e}")
