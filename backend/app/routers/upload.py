from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Any

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
async def upload_xlsx_file(file: UploadFile = File(...)):
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
                },
            )

        # Adattípusok validálása
        data_type_errors = TransactionFileValidator.validate_data_types(df)
        validation_warnings.extend(data_type_errors)

        # Kötelező mezők validálása
        required_data_errors = TransactionFileValidator.validate_required_data(df)
        validation_errors.extend(required_data_errors)

        # 7. Alapvető statisztikák
        stats = {
            "total_transactions": int(len(df)),
            "date_range": {
                "earliest": (
                    str(df["Tranzakció dátuma"].min())
                    if not df["Tranzakció dátuma"].isna().all()
                    else None
                ),
                "latest": (
                    str(df["Tranzakció dátuma"].max())
                    if not df["Tranzakció dátuma"].isna().all()
                    else None
                ),
            },
            "amount_summary": {
                "total": (
                    float(df["Összeg"].sum())
                    if "Összeg" in df.columns and not df["Összeg"].isna().all()
                    else 0
                ),
                "positive_count": (
                    int((df["Összeg"] > 0).sum()) if "Összeg" in df.columns else 0
                ),
                "negative_count": (
                    int((df["Összeg"] < 0).sum()) if "Összeg" in df.columns else 0
                ),
                "min_amount": (
                    float(df["Összeg"].min())
                    if "Összeg" in df.columns and not df["Összeg"].isna().all()
                    else 0
                ),
                "max_amount": (
                    float(df["Összeg"].max())
                    if "Összeg" in df.columns and not df["Összeg"].isna().all()
                    else 0
                ),
            },
            "currencies": (
                {str(k): int(v) for k, v in df["Pénznem"].value_counts().items()}
                if "Pénznem" in df.columns
                else {}
            ),
            "directions": (
                {str(k): int(v) for k, v in df["Bejövő/Kimenő"].value_counts().items()}
                if "Bejövő/Kimenő" in df.columns
                else {}
            ),
        }

        # 8. Alapvető adatok kinyerése
        file_info = {
            "filename": file.filename,
            "file_size_mb": round(file.size / (1024 * 1024), 2),
            "rows_count": int(len(df)),
            "columns_count": int(len(df.columns)),
            "columns": [str(col) for col in df.columns],
            "first_3_rows": df.head(3).fillna("").to_dict("records"),
            "data_types": {str(k): str(v) for k, v in df.dtypes.items()},
            "empty_rows_removed": int(
                pd.read_excel(io.BytesIO(file_content), engine="openpyxl")
                .isnull()
                .all(axis=1)
                .sum()
            ),
            "has_data": not df.empty,
        }

        # 9. Válasz összeállítása
        response = {
            "success": len(validation_errors) == 0,
            "message": f"Fájl feldolgozva: {len(validation_errors)} hiba, {len(validation_warnings)} figyelmeztetés",
            "file_info": file_info,
            "statistics": stats,
            "validation": {
                "errors": validation_errors,
                "warnings": validation_warnings,
                "is_valid": len(validation_errors) == 0,
            },
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
