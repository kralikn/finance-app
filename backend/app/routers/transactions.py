from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from app.database.database import get_db
from app.database.models import Transaction, Category

# Router létrehozása
router = APIRouter(prefix="/transactions", tags=["transactions"])


# Segédfüggvény a Transaction dict-té alakításához
def transaction_to_dict(transaction: Transaction) -> Dict[str, Any]:
    return {
        "id": transaction.id,
        "transaction_date": (
            transaction.transaction_date.isoformat()
            if transaction.transaction_date
            else None
        ),
        "booking_date": (
            transaction.booking_date.isoformat() if transaction.booking_date else None
        ),
        "transaction_type": transaction.transaction_type,
        "direction": transaction.direction,
        "partner_name": transaction.partner_name,
        "partner_account": transaction.partner_account,
        "expense_category": transaction.expense_category,
        "description": transaction.description,
        "account_name": transaction.account_name,
        "account_number": transaction.account_number,
        "amount": float(transaction.amount) if transaction.amount else 0.0,
        "currency": transaction.currency,
        "category_id": transaction.category_id,
        "created_at": (
            transaction.created_at.isoformat() if transaction.created_at else None
        ),
        "updated_at": (
            transaction.updated_at.isoformat() if transaction.updated_at else None
        ),
    }


# CREATE - Új Transaction létrehozása (upload-ból jövő adatokhoz)
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_date: str,
    amount: float,
    direction: str,
    partner_name: str = None,
    booking_date: str = None,
    transaction_type: str = None,
    partner_account: str = None,
    expense_category: str = None,
    description: str = None,
    account_name: str = None,
    account_number: str = None,
    currency: str = "HUF",
    category_id: int = None,
    db: Session = Depends(get_db),
):
    """Új tranzakció létrehozása"""

    # Dátum konvertálás
    try:
        trans_date = datetime.fromisoformat(transaction_date).date()
        book_date = (
            datetime.fromisoformat(booking_date).date() if booking_date else None
        )
    except ValueError:
        raise HTTPException(400, "Érvénytelen dátum formátum")

    # Új Transaction létrehozása
    db_transaction = Transaction(
        transaction_date=trans_date,
        booking_date=book_date,
        transaction_type=transaction_type or "",
        direction=direction,
        partner_name=partner_name,
        partner_account=partner_account,
        expense_category=expense_category,
        description=description,
        account_name=account_name,
        account_number=account_number,
        amount=Decimal(str(amount)),
        currency=currency,
        category_id=category_id,
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return transaction_to_dict(db_transaction)


# CREATE BULK - Több tranzakció egyszerre (upload-hoz)
@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def create_transactions_bulk(
    transactions: List[Dict[str, Any]], db: Session = Depends(get_db)
):
    """Több tranzakció egyszerre létrehozása (upload-ból)"""

    created_transactions = []

    for trans_data in transactions:
        # Csak a nem duplikált tranzakciókat mentjük
        if trans_data.get("is_duplicate", False):
            continue

        try:
            # Dátum konvertálás
            trans_date = datetime.fromisoformat(trans_data["transaction_date"]).date()
            book_date = None
            if trans_data.get("booking_date"):
                book_date = datetime.fromisoformat(trans_data["booking_date"]).date()

            # Kategória ID kinyerése suggested_category-ből
            category_id = None
            if trans_data.get("suggested_category"):
                category_id = trans_data["suggested_category"]["id"]

            # Transaction létrehozása
            db_transaction = Transaction(
                transaction_date=trans_date,
                booking_date=book_date,
                transaction_type=trans_data.get("transaction_type", ""),
                direction=trans_data.get("direction", ""),
                partner_name=trans_data.get("partner_name"),
                partner_account=trans_data.get("partner_account"),
                expense_category=trans_data.get("expense_category"),
                description=trans_data.get("description"),
                account_name=trans_data.get("account_name"),
                account_number=trans_data.get("account_number"),
                amount=Decimal(str(trans_data.get("amount", 0))),
                currency=trans_data.get("currency", "HUF"),
                category_id=category_id,
            )

            db.add(db_transaction)
            created_transactions.append(db_transaction)

        except Exception as e:
            # Hibás tranzakciót kihagyjuk
            continue

    db.commit()

    # Refresh minden létrehozott tranzakcióra
    for trans in created_transactions:
        db.refresh(trans)

    return {
        "created_count": len(created_transactions),
        "transactions": [transaction_to_dict(t) for t in created_transactions],
    }


# READ - Összes Transaction lekérése
@router.get("/")
def get_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Tranzakciók lekérése"""
    transactions = (
        db.query(Transaction)
        .order_by(Transaction.transaction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [transaction_to_dict(t) for t in transactions]


# READ - Egy Transaction lekérése ID alapján
@router.get("/{transaction_id}")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Egy tranzakció lekérése"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction nem található ID: {transaction_id}",
        )

    return transaction_to_dict(transaction)


# UPDATE - Transaction módosítása (főleg kategória beállításhoz)
@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    category_id: int = None,
    partner_name: str = None,
    description: str = None,
    expense_category: str = None,
    db: Session = Depends(get_db),
):
    """Tranzakció módosítása (főleg kategória beállítás)"""

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction nem található ID: {transaction_id}",
        )

    # Módosítások alkalmazása
    if category_id is not None:
        transaction.category_id = category_id
    if partner_name is not None:
        transaction.partner_name = partner_name
    if description is not None:
        transaction.description = description
    if expense_category is not None:
        transaction.expense_category = expense_category

    db.commit()
    db.refresh(transaction)

    return transaction_to_dict(transaction)


# UPDATE BULK - Több tranzakció kategória beállítása egyszerre
@router.put("/bulk/category")
def update_transactions_category(
    transaction_ids: List[int], category_id: int, db: Session = Depends(get_db)
):
    """Több tranzakció kategóriájának beállítása egyszerre"""

    updated_count = (
        db.query(Transaction)
        .filter(Transaction.id.in_(transaction_ids))
        .update({Transaction.category_id: category_id}, synchronize_session=False)
    )

    db.commit()

    return {"updated_count": updated_count, "category_id": category_id}


# DELETE - Transaction törlése
@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Tranzakció törlése"""

    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction nem található ID: {transaction_id}",
        )

    db.delete(transaction)
    db.commit()


# EXTRA - Kategória nélküli tranzakciók lekérése
@router.get("/uncategorized/")
def get_uncategorized_transactions(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Kategória nélküli tranzakciók lekérése"""

    transactions = (
        db.query(Transaction)
        .filter(Transaction.category_id.is_(None))
        .order_by(Transaction.transaction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [transaction_to_dict(t) for t in transactions]
