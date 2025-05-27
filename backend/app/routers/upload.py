from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Any
from app.database.models import Category, CategoryKeyword, Transaction
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter(prefix="/upload", tags=["upload"])


class TransactionFileValidator:
    """Tranzakciós fájl validátor osztály"""

    # Elvárt oszlopnevek a minta fájl alapján
    REQUIRED_COLUMNS = [
        "Tranzakció dátuma",
        "Könyvelés dátuma",
        "Típus",
        "Bejövő/Kimenő",
        "Partner neve",
        "Partner számlaszáma/azonosítója",
        "Költési kategória",
        "Közlemény",
        "Számla név",
        "Számla szám",
        "Összeg",
        "Pénznem",
    ]

    @staticmethod
    def validate_columns(df: pd.DataFrame) -> List[str]:
        """Oszlopok validálása"""
        errors = []

        # Oszlopnevek tisztítása (extra szóközök eltávolítása)
        df.columns = df.columns.str.strip()

        # Hiányzó kötelező oszlopok
        missing_columns = []
        for required_col in TransactionFileValidator.REQUIRED_COLUMNS:
            if required_col not in df.columns:
                missing_columns.append(required_col)

        if missing_columns:
            errors.append(f"Hiányzó kötelező oszlopok: {missing_columns}")

        # Extra oszlopok figyelmeztetése
        extra_columns = [
            col
            for col in df.columns
            if col not in TransactionFileValidator.REQUIRED_COLUMNS
        ]
        if extra_columns:
            errors.append(
                f"Ismeretlen oszlopok (figyelmen kívül lesznek hagyva): {extra_columns}"
            )

        return errors

    @staticmethod
    def validate_data_types(df: pd.DataFrame) -> List[str]:
        """Adattípusok validálása"""
        errors = []

        # Összeg oszlop ellenőrzése
        if "Összeg" in df.columns:
            non_numeric_amounts = df[
                df["Összeg"].notna()
                & ~df["Összeg"].apply(lambda x: isinstance(x, (int, float)))
            ]["Összeg"]
            if not non_numeric_amounts.empty:
                errors.append(
                    f"Nem numerikus értékek az Összeg oszlopban: {non_numeric_amounts.head().tolist()}"
                )

        # Pénznem oszlop ellenőrzése
        if "Pénznem" in df.columns:
            unique_currencies = df["Pénznem"].dropna().unique()
            invalid_currencies = [
                curr for curr in unique_currencies if len(str(curr)) != 3
            ]
            if invalid_currencies:
                errors.append(
                    f"Érvénytelen pénznem kódok (nem 3 karakter): {invalid_currencies}"
                )

        # Irány oszlop ellenőrzése
        if "Bejövő/Kimenő" in df.columns:
            valid_directions = ["Bejövő", "Kimenő"]
            invalid_directions = (
                df[~df["Bejövő/Kimenő"].isin(valid_directions)]["Bejövő/Kimenő"]
                .dropna()
                .unique()
            )
            if len(invalid_directions) > 0:
                errors.append(
                    f"Érvénytelen irány értékek: {invalid_directions.tolist()}"
                )

        return errors

    @staticmethod
    def validate_required_data(df: pd.DataFrame) -> List[str]:
        """Kötelező mezők kitöltöttségének ellenőrzése"""
        errors = []

        critical_columns = ["Tranzakció dátuma", "Összeg", "Bejövő/Kimenő", "Pénznem"]

        for col in critical_columns:
            if col in df.columns:
                empty_count = df[col].isna().sum()
                if empty_count > 0:
                    errors.append(
                        f"'{col}' oszlopban {empty_count} üres érték található"
                    )

        return errors


@router.post("/")
async def upload_xlsx_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Excel fájl feltöltése és adatok kinyerése
    """

    # 1. Fájl típus validálás
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Csak Excel fájlok (.xlsx, .xls) engedélyezettek"
        )

    # 2. Fájl méret ellenőrzés (10MB limit)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fájl túl nagy (maximum 10MB)")

    try:
        # 3. Fájl beolvasása
        file_content = await file.read()

        # 4. Pandas DataFrame létrehozása
        df = pd.read_excel(io.BytesIO(file_content), engine="openpyxl")

        # 5. Üres sorok eltávolítása
        df = df.dropna(how="all")

        if df.empty:
            raise HTTPException(status_code=400, detail="A fájl nem tartalmaz adatokat")

        # 6. VALIDÁLÁS
        validation_errors = []
        validation_warnings = []

        # Oszlopok validálása
        column_errors = TransactionFileValidator.validate_columns(df)
        validation_errors.extend(column_errors)

        # Ha alapvető oszlopstruktúra hibás, itt megállunk
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Fájlstruktúra hibás",
                    "errors": validation_errors,
                    "available_columns": [str(col) for col in df.columns],
                    "suggested_category": None,
                    "is_duplicate": False,
                },
            )

        # Adattípusok validálása
        data_type_errors = TransactionFileValidator.validate_data_types(df)
        validation_warnings.extend(data_type_errors)

        # Kötelező mezők validálása
        required_data_errors = TransactionFileValidator.validate_required_data(df)
        validation_errors.extend(required_data_errors)

        # 7. Auto-kategorizálás és duplikáció ellenőrzés
        transactions_data = await process_transactions(df, db)

        # 8. Válasz összeállítása
        response = {
            "success": True,
            "message": f"Fájl feldolgozva: {len(df)} tranzakció, {transactions_data['duplicates']['count']} duplikátum",
            "transactions": transactions_data["transactions"],
            "duplicates": transactions_data["duplicates"],
            "validation": {"warnings": validation_warnings, "is_valid": True},
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Hiba a fájl feldolgozása során: {str(e)}"
        )

    finally:
        # 10. Fájl stream bezárása
        await file.close()


async def process_transactions(df: pd.DataFrame, db: Session) -> Dict:
    """
    Tranzakciók feldolgozása: kategorizálás + duplikáció ellenőrzés
    """

    # 1. Kategorizálás
    transactions = await categorize_transactions(df, db)

    # 2. Duplikáció ellenőrzés
    duplicates = await check_duplicates(transactions, db)

    return {"transactions": transactions, "duplicates": duplicates}


async def categorize_transactions(df: pd.DataFrame, db: Session) -> List[Dict]:
    """
    Tranzakciók kategorizálása Partner neve alapján keywords matching-gel
    """

    # Összes kategória és kulcsszavak lekérése
    categories_with_keywords = db.query(Category).join(CategoryKeyword).all()

    # Keywords map építése (kulcsszó -> kategória)
    keyword_to_category = {}
    for category in categories_with_keywords:
        for keyword_obj in category.keywords:
            keyword_to_category[keyword_obj.keyword.upper()] = {
                "id": category.id,
                "name": category.name,
                "type": category.type,
            }

    transactions = []

    for index, row in df.iterrows():
        # Alapvető tranzakció adatok
        transaction = {
            "row_number": index + 1,
            "transaction_date": str(row["Tranzakció dátuma"]),
            "booking_date": (
                str(row["Könyvelés dátuma"])
                if pd.notna(row["Könyvelés dátuma"])
                else None
            ),
            "transaction_type": str(row["Típus"]) if pd.notna(row["Típus"]) else "",
            "direction": (
                str(row["Bejövő/Kimenő"]) if pd.notna(row["Bejövő/Kimenő"]) else ""
            ),
            "partner_name": (
                str(row["Partner neve"]) if pd.notna(row["Partner neve"]) else ""
            ),
            "partner_account": (
                str(row["Partner számlaszáma/azonosítója"])
                if pd.notna(row["Partner számlaszáma/azonosítója"])
                else ""
            ),
            "expense_category": (
                str(row["Költési kategória"])
                if pd.notna(row["Költési kategória"])
                else ""
            ),
            "description": str(row["Közlemény"]) if pd.notna(row["Közlemény"]) else "",
            "account_name": (
                str(row["Számla név"]) if pd.notna(row["Számla név"]) else ""
            ),
            "account_number": (
                str(row["Számla szám"]) if pd.notna(row["Számla szám"]) else ""
            ),
            "amount": float(row["Összeg"]) if pd.notna(row["Összeg"]) else 0.0,
            "currency": str(row["Pénznem"]) if pd.notna(row["Pénznem"]) else "HUF",
            "suggested_category": None,
        }

        # Kategória keresés Partner neve alapján
        partner_name = transaction["partner_name"].upper()

        if partner_name:
            # Kulcsszó keresés a partner névben
            found_category = None
            for keyword, category_info in keyword_to_category.items():
                if keyword in partner_name:
                    found_category = category_info
                    break

            if found_category:
                transaction["suggested_category"] = found_category

        transactions.append(transaction)

    return transactions


async def check_duplicates(transactions: List[Dict], db: Session) -> Dict:
    """
    Duplikáció ellenőrzés meglévő tranzakciók alapján
    Matching: transaction_date + amount + partner_name
    """

    duplicate_info = {"count": 0, "transactions": []}

    for transaction in transactions:
        # Duplikáció keresés az adatbázisban
        existing_transaction = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_date == transaction["transaction_date"],
                Transaction.amount == transaction["amount"],
                Transaction.partner_name == transaction["partner_name"],
            )
            .first()
        )

        if existing_transaction:
            duplicate_info["count"] += 1
            duplicate_info["transactions"].append(
                {
                    "row_number": transaction["row_number"],
                    "partner_name": transaction["partner_name"],
                    "amount": transaction["amount"],
                    "transaction_date": transaction["transaction_date"],
                    "existing_id": existing_transaction.id,
                    "is_duplicate": True,
                }
            )

            # Eredeti tranzakcióhoz is jelöljük
            transaction["is_duplicate"] = True
            transaction["existing_transaction_id"] = existing_transaction.id
        else:
            transaction["is_duplicate"] = False

    return duplicate_info
