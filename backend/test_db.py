# Tesztelő script (test_db.py)
from app.database.database import engine, Base
from sqlalchemy import text

try:
    # Connection teszt
    with engine.connect() as connection:
        result = connection.execute(text("SELECT @@VERSION"))
        version = result.fetchone()[0]

        print("✅ Database connection successful!")
        print(f"Database version: {version}")

        # További tesztek
        result2 = connection.execute(text("SELECT DB_NAME() as DatabaseName"))
        db_name = result2.fetchone()[0]
        print(f"Connected to database: {db_name}")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
