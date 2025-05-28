# Finance App

Személyes pénzügyi elemző alkalmazás - banki tranzakciók feltöltése és elemzése.

## 🚀 Technológiák

- **Backend:** FastAPI (Python)
- **Frontend:** Next.js 15 (JavaScript)
- **Database:** Azure SQL Database
- **Hosting:** Azure App Service + Vercel

## 🏃‍♂️ Gyors Start

### Backend
```bash
cd backend

# Virtual environment
python -m venv venv
source venv\Scripts\activate  # Windows

# Dependencies
pip install -r requirements.txt

# Database setup (egyszer futtatni)
python create_tables.py
python seed_categories.py

# API indítása
fastapi dev main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
**backend/.env:**
```env
DB_SERVER=your-server.database.windows.net
DB_DATABASE=financeapp_db
DB_USERNAME=your_username
DB_PASSWORD=your_password
DEBUG=True
FRONTEND_URL=http://localhost:3000
```

## 📱 Elérhető URL-ek

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Categories API:** http://localhost:8000/api/categories
- **Category Keywords API:** http://localhost:8000/api/category-keywords
- **Transactions API:** http://localhost:8000/api/transactions
- **Upload API:** http://localhost:8000/api/upload



## 🗄️ Database Schema

### Categories Table
```sql
- id (Primary Key)
- name (Kategória neve)
- type ('income' vagy 'expense')
- created_at (Létrehozás dátuma)
```

### Category Keywords Table (Junction Table)
```sql
- id (Primary Key)
- category_id (FK -> categories.id, Indexed)
- keyword (Unicode kulcsszó automatikus matching-hez, Indexed)
```

### Transactions Table
```sql
- id (Primary Key)
- transaction_date (Tranzakció dátuma, Indexed)
- booking_date (Könyvelés dátuma)
- transaction_type (Típus)
- direction ('Bejövő' vagy 'Kimenő')
- partner_name (Partner neve)
- partner_account (Partner számlaszáma)
- expense_category (Bank eredeti kategóriája)
- description (Közlemény)
- account_name (Számla név)
- account_number (Számla szám)
- amount (Összeg, Numeric(15,2), Indexed)
- currency (Pénznem, default: HUF)
- category_id (FK -> categories.id, Indexed)
- created_at, updated_at (Timestamps)
```

## 🔧 Implementált Funkciók

### ✅ Categories API (Teljes CRUD)
- **GET /api/categories** - Összes kategória lekérése (type és name szerint rendezve)
- **GET /api/categories/{id}** - Egy kategória lekérése ID alapján
- **POST /api/categories** - Új kategória létrehozása (keywords támogatással)
- **PUT /api/categories/{id}** - Kategória módosítása (név, típus, keywords)
- **DELETE /api/categories/{id}** - Kategória törlése (reassign_to paraméterrel)

#### Categories API Funkciók:
- **Duplikáció védelem:** Név + típus kombináció egyediségének biztosítása
- **Cascade törlés:** Keywords automatikus törlése kategória törlésekor
- **Tranzakció reassign:** Kategória törlésekor tranzakciók átállítása másik kategóriára
- **Típus validáció:** Csak 'income' és 'expense' típusok engedélyezettek
- **Cross-type védelem:** Income kategóriát nem lehet expense-re reassignolni


### ✅ Category Keywords API (CRUD)
- **GET /api/category-keywords** - Összes kulcsszó lekérése (pagination-nel)
- **GET /api/category-keywords/{id}** - Egy kulcsszó lekérése ID alapján
- **POST /api/category-keywords** - Új kulcsszó létrehozása kategóriához
- **PUT /api/category-keywords/{id}** - Kulcsszó módosítása
- **DELETE /api/category-keywords/{id}** - Kulcsszó törlése
- **DELETE /api/category-keywords/category/{id}** - Egy kategória összes kulcsszavának törlése

#### Category Keywords API Funkciók:
- **MVP optimalizáció:** Minimális validálás, egyszerű paraméter átadás
- **MSSQL kompatibilitás:** ORDER BY automatikus hozzáadása pagination-höz
- **Duplikáció védelem:** Ugyanaz a kulcsszó nem lehet kétszer egy kategóriánál

### ✅ Transactions API (Teljes CRUD)
- **GET /api/transactions** - Összes tranzakció lekérése (dátum szerint rendezve, pagination)
- **GET /api/transactions/{id}** - Egy tranzakció lekérése ID alapján
- **POST /api/transactions** - Új tranzakció létrehozása
- **POST /api/transactions/bulk** - Több tranzakció egyszerre (upload integráció)
- **PUT /api/transactions/{id}** - Tranzakció módosítása (főleg kategória beállítás)
- **PUT /api/transactions/bulk/category** - Több tranzakció kategóriájának beállítása
- **DELETE /api/transactions/{id}** - Tranzakció törlése
- **GET /api/transactions/uncategorized** - Kategória nélküli tranzakciók

#### Transactions API Funkciók:
- **Upload integráció:** Bulk endpoint az upload workflow-hoz optimalizálva
- **Duplikáció kezelés:** Automatikusan kihagyja a duplikált tranzakciókat
- **Auto-kategorizálás:** Upload-ból jövő suggested_category automatikus alkalmazása
- **Bulk műveletek:** Hatékony tömeges kategória beállítás
- **MVP optimalizáció:** Minimális validálás, gyors fejlesztéshez

### ✅ File Upload API (.xlsx feldolgozás)
- **POST /api/upload/xlsx** - Excel fájl feltöltése és validálása
- **Támogatott formátumok:** .xlsx, .xls (max 10MB)
- **Automatikus adattisztítás:** Üres sorok eltávolítása, típus normalizálás
- **Oszlop validálás:** 12 kötelező banki oszlop ellenőrzése
- **Adattípus validálás:** Összeg (numerikus), Pénznem (3 karakter), Irány (Bejövő/Kimenő)
- **Kötelező mezők:** Tranzakció dátuma, Összeg, Irány, Pénznem kitöltöttség
- **Auto-kategorizálás:** Partner neve alapján keywords matching
- **Duplikáció ellenőrzés:** Meglévő tranzakciókkal összehasonlítás
- **Hibajelentés:** Részletes validációs hibák és figyelmeztetések


### ✅ Database
- Azure SQL Database kapcsolat
- SQLAlchemy modellek (CategoryKeyword, Category, Transaction)
- Relationship-ek Foreign Key-ekkel
- Auto-generated timestamps

### ✅ Development Tools
- Database connection teszt
- Table creation script
- Category seeding script
- Swagger API dokumentáció


## 📋 Development Status

- [x] Projekt setup és Git repository
- [x] Backend-Frontend kommunikáció
- [x] Azure SQL Database kapcsolat
- [x] SQLAlchemy modellek (CategoryKeyword, Category, Transaction)
- [x] Categories CRUD API
- [x] **Category Keywords CRUD API**
- [x] Default kategóriák seedelése
- [x] **File upload funkció (.xlsx parsing)**
- [x] **Upload API validációs rendszer**
- [x] **Auto-kategorizálás** - Keywords alapú automatikus kategorizálás
- [x] **Duplikáció ellenőrzés** - Meglévő tranzakciók felismerése
- [x] **Transaction CRUD API** - Teljes CRUD + bulk műveletek
- [x] **Upload-Transaction integráció** - Seamless workflow
- [ ] Frontend transaction management
- [ ] Adatvizualizáció (Charts)
- [ ] AI elemzési funkciók


## 📝 Next Steps

1. **Frontend Integration** - Transaction management UI
2. **Categories dropdown** - Frontend kategória választó
3. **Data Visualization** - Charts és grafikonok
4. **AI Analysis** - Költési szokások elemzése

---

🔧 **Sprint 6 Complete** - Transaction API és Category Keywords API kész  
📈 **Next Sprint** - Frontend integration és Transaction management UI

🔧 **Work in Progress** - MVP fejlesztés alatt