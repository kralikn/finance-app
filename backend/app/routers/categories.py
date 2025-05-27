from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Category
from typing import List

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    """Összes kategória lekérése"""
    categories = db.query(Category).order_by(Category.type, Category.name).all()
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "type": cat.type,
            "created_at": cat.created_at.isoformat(),
        }
        for cat in categories
    ]


@router.post("/")
def create_category(name: str, type: str, db: Session = Depends(get_db)):
    """Új kategória létrehozása"""
    if type not in ["income", "expense"]:
        raise HTTPException(400, "Type must be 'income' or 'expense'")

    # Ellenőrzés: létezik-e már ilyen nevű
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(400, f"Category '{name}' already exists")

    category = Category(name=name, type=type)
    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "type": category.type,
        "created_at": category.created_at.isoformat(),
    }
