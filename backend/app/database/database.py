from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import urllib

import os
from dotenv import load_dotenv

load_dotenv()

server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = "ODBC+Driver+17+for+SQL+Server"


password = urllib.parse.quote_plus(password)


engine = create_engine(
    f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver={driver}&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=60",
    echo=True if os.getenv("DEBUG") == "True" else False,  # SQL logolás debug módban
    pool_pre_ping=True,  # Connection health check
    pool_recycle=300,  # Connection refresh 5 percenként)
    pool_timeout=60,  # Connection pool timeout
    connect_args={
        "timeout": 60,  # PyODBC timeout
    },
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
