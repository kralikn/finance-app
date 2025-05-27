from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Category, CategoryKeyword
from typing import List, Optional

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
            "keywords": [kw.keyword for kw in cat.keywords],
            "created_at": cat.created_at.isoformat(),
        }
        for cat in categories
    ]


@router.get("/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Egy kategória lekérése ID alapján"""
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(404, f"Category with id {category_id} not found")

    return {
        "id": category.id,
        "name": category.name,
        "type": category.type,
        "keywords": [kw.keyword for kw in category.keywords],
        "created_at": category.created_at.isoformat(),
        # "transaction_count": len(category.transactions),  # Hány tranzakció használja
    }


@router.post("/")
def create_category(
    name: str, type: str, keywords: List[str] = None, db: Session = Depends(get_db)
):
    """Új kategória létrehozása"""
    if type not in ["income", "expense"]:
        raise HTTPException(400, "Type must be 'income' or 'expense'")

    # Ellenőrzés: létezik-e már ilyen név + típus kombináció
    existing = (
        db.query(Category).filter(Category.name == name, Category.type == type).first()
    )

    if existing:
        raise HTTPException(400, f"Category '{name}' with type '{type}' already exists")

    category = Category(name=name, type=type)

    # Keywords hozzáadása ha vannak
    if keywords:
        for keyword in keywords:
            if keyword.strip():  # Üres string ellenőrzés
                category_keyword = CategoryKeyword(keyword=keyword.strip().upper())
                # category_keyword = CategoryKeyword(keyword=keyword.strip())
                category.keywords.append(category_keyword)

    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "type": category.type,
        "created_at": category.created_at.isoformat(),
    }


@router.put("/{category_id}")
def update_category(
    category_id: int,
    name: Optional[str] = None,
    type: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    db: Session = Depends(get_db),
):
    """Kategória módosítása"""
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(404, f"Category with id {category_id} not found")

    # Név és típus frissítése
    if name is not None:
        category.name = name

    if type is not None:
        if type not in ["income", "expense"]:
            raise HTTPException(400, "Type must be 'income' or 'expense'")
        category.type = type

    # Keywords frissítése (teljes csere)
    if keywords is not None:
        # Régi keywords törlése (cascade miatt automatikus)
        category.keywords.clear()

        # Új keywords hozzáadása
        for keyword in keywords:
            if keyword.strip():
                category_keyword = CategoryKeyword(keyword=keyword.strip().upper())
                category.keywords.append(category_keyword)

    # Duplikáció ellenőrzése név+típus alapján
    if name or type:
        existing = (
            db.query(Category)
            .filter(
                Category.name == category.name,
                Category.type == category.type,
                Category.id != category_id,  # Saját magát kizárjuk
            )
            .first()
        )

        if existing:
            raise HTTPException(
                400,
                f"Category '{category.name}' with type '{category.type}' already exists",
            )

    db.commit()
    db.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "type": category.type,
        "keywords": [kw.keyword for kw in category.keywords],
        "created_at": category.created_at.isoformat(),
    }


@router.delete("/{category_id}")
def delete_category(
    category_id: int, reassign_to: int = None, db: Session = Depends(get_db)
):
    """Kategória törlése"""
    category = db.query(Category).filter(Category.id == category_id).first()

    if not category:
        raise HTTPException(404, f"Category with id {category_id} not found")

    # Ellenőrzés: van-e használatban (tranzakciókhoz rendelve)
    transaction_count = len(category.transactions)
    if transaction_count > 0:
        if reassign_to:
            # Ellenőrzés: létezik-e a célkategória
            new_category = db.query(Category).filter(Category.id == reassign_to).first()
            if not new_category:
                raise HTTPException(
                    400, f"Target category with id {reassign_to} not found"
                )

            # Típus ellenőrzése (income kategóriát ne lehessen expense-re állítani)
            if category.type != new_category.type:
                raise HTTPException(
                    400,
                    f"Cannot reassign {category.type} category to {new_category.type} category",
                )

            # Tranzakciók átállítása
            for transaction in category.transactions:
                transaction.category_id = reassign_to

            message = f"Category '{category.name}' deleted. {transaction_count} transactions reassigned to '{new_category.name}'"

        else:
            # NULL-ra állítás (kategorizálatlan)
            for transaction in category.transactions:
                transaction.category_id = None

            message = f"Category '{category.name}' deleted. {transaction_count} transactions set to uncategorized"
    else:
        message = f"Category '{category.name}' deleted successfully (no transactions affected)"

    db.delete(category)  # Keywords automatikusan törlődnek (cascade)
    db.commit()

    return {
        "message": message,
        "deleted_id": category_id,
        "affected_transactions": transaction_count,
        "reassigned_to": reassign_to if reassign_to else None,
    }
