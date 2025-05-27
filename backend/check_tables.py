# check_tables.py
from app.database.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Táblák listázása
    result = conn.execute(
        text(
            """
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME IN ('categories', 'transactions')
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
        )
    )

    current_table = None
    for row in result:
        table, column, data_type = row
        if table != current_table:
            print(f"\n📋 {table}:")
            current_table = table
        print(f"  - {column}: {data_type}")
