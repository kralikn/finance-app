from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database.database import get_db
from app.database.models import Category, CategoryKeyword

# Router létrehozása
router = APIRouter(prefix="/category-keywords", tags=["category-keywords"])


# Segédfüggvény a CategoryKeyword dict-té alakításához
def keyword_to_dict(keyword: CategoryKeyword) -> Dict[str, Any]:
    return {
        "id": keyword.id,
        "category_id": keyword.category_id,
        "keyword": keyword.keyword,
    }


# CREATE - Új CategoryKeyword létrehozása
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_category_keyword(
    category_id: int, keyword: str, db: Session = Depends(get_db)
):
    # Alapvető validálás
    if not keyword or not category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_id és keyword mezők kötelezőek",
        )

    # Típus és érték ellenőrzés
    if not isinstance(category_id, int) or category_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category_id pozitív egész szám kell legyen",
        )

    if not keyword or len(keyword.strip()) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="keyword nem lehet üres és maximum 100 karakter lehet",
        )

    # Ellenőrizzük, hogy létezik-e a kategória
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kategória nem található ID: {category_id}",
        )

    # Ellenőrizzük, hogy már létezik-e ez a kulcsszó ehhez a kategóriához
    existing_keyword = (
        db.query(CategoryKeyword)
        .filter(
            CategoryKeyword.category_id == category_id,
            CategoryKeyword.keyword == keyword,
        )
        .first()
    )

    if existing_keyword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ez a kulcsszó már létezik ehhez a kategóriához",
        )

    # Új CategoryKeyword létrehozása
    db_keyword = CategoryKeyword(
        category_id=category_id, keyword=keyword.strip().upper()
    )

    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)

    return keyword_to_dict(db_keyword)


# READ - Összes CategoryKeyword lekérése
@router.get("/")
def get_category_keywords(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    keywords = (
        db.query(CategoryKeyword)
        .order_by(CategoryKeyword.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [keyword_to_dict(kw) for kw in keywords]


# READ - Egy CategoryKeyword lekérése ID alapján
@router.get("/{keyword_id}")
def get_category_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(CategoryKeyword).filter(CategoryKeyword.id == keyword_id).first()

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CategoryKeyword nem található ID: {keyword_id}",
        )

    return keyword_to_dict(keyword)


# UPDATE - CategoryKeyword módosítása
@router.put("/{keyword_id}")
def update_category_keyword(
    keyword_id: int, keyword: str, db: Session = Depends(get_db)
):
    existing = (
        db.query(CategoryKeyword).filter(CategoryKeyword.id == keyword_id).first()
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CategoryKeyword nem található ID: {keyword_id}",
        )

    # Alapvető validálás
    if not keyword or len(keyword.strip()) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="keyword nem lehet üres és maximum 100 karakter lehet",
        )

    # Ellenőrizzük, hogy nem létezik-e már ez a kulcsszó ugyanahhoz a kategóriához
    existing_keyword = (
        db.query(CategoryKeyword)
        .filter(
            CategoryKeyword.category_id == existing.category_id,
            CategoryKeyword.keyword == keyword.strip(),
            CategoryKeyword.id != keyword_id,  # Kivéve a jelenlegi rekordot
        )
        .first()
    )

    if existing_keyword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ez a kulcsszó már létezik ehhez a kategóriához",
        )

    existing.keyword = keyword.strip().upper()

    db.commit()
    db.refresh(existing)

    return keyword_to_dict(existing)


# DELETE - CategoryKeyword törlése
@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(CategoryKeyword).filter(CategoryKeyword.id == keyword_id).first()

    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CategoryKeyword nem található ID: {keyword_id}",
        )

    db.delete(keyword)
    db.commit()


# EXTRA - Egy kategória összes kulcsszavának törlése
@router.delete("/category/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_keywords_by_category(category_id: int, db: Session = Depends(get_db)):
    # Ellenőrizzük, hogy létezik-e a kategória
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kategória nem található ID: {category_id}",
        )

    # Töröljük az összes kulcsszót
    deleted_count = (
        db.query(CategoryKeyword)
        .filter(CategoryKeyword.category_id == category_id)
        .delete()
    )

    db.commit()
