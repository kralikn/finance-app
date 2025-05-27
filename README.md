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

## 🗄️ Database Schema

### Categories Table
```sql
- id (Primary Key)
- name (Kategória neve)
- type ('income' vagy 'expense')
- created_at (Létrehozás dátuma)
```

### Transactions Table
```sql
- id (Primary Key)
- transaction_date (Tranzakció dátuma)
- booking_date (Könyvelés dátuma)
- transaction_type (Típus)
- direction ('Bejövő' vagy 'Kimenő')
- partner_name (Partner neve)
- partner_account (Partner számlaszáma)
- expense_category (Bank eredeti kategóriája)
- description (Közlemény)
- account_name (Számla név)
- account_number (Számla szám)
- amount (Összeg)
- currency (Pénznem, default: HUF)
- category_id (FK -> categories.id)
- created_at, updated_at (Timestamps)
```
## 🔧 Implementált Funkciók

### ✅ Categories API
- **GET /api/categories** - Összes kategória lekérése
- **POST /api/categories** - Új kategória létrehozása
- Default kategóriák: Fizetés, Élelmiszer, Lakhatás, stb.

### ✅ Database
- Azure SQL Database kapcsolat
- SQLAlchemy modellek (Category, Transaction)
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
- [x] SQLAlchemy modellek (Category, Transaction)
- [x] Categories CRUD API
- [x] Default kategóriák seedelése
- [ ] File upload funkció (.xlsx parsing)
- [ ] Transaction CRUD API
- [ ] Frontend transaction management
- [ ] Adatvizualizáció (Charts)
- [ ] AI elemzési funkciók

## 📝 Next Steps

1. **Excel File Upload** - Banki tranzakciók feltöltése
2. **Transaction Management** - CRUD műveletek
3. **Frontend Integration** - Categories dropdown
4. **Data Visualization** - Charts és grafikonok
5. **AI Analysis** - Költési szokások elemzése

---

🔧 **Sprint 2 Complete** - Database és Categories API kész  
📈 **Next Sprint** - File Upload és Transaction Management

🔧 **Work in Progress** - MVP fejlesztés alatt