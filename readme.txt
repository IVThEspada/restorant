# Restaurant Ordering System (Backend)

uvicorn app.main:app --reload

## Kurulum

1. Python 3.10+ kurulu olmalı
2. PostgreSQL kur → `restaurant` adında veritabanı oluştur
3. Veritabanı bilgileri:
   - kullanıcı: `postgres`
   - şifre: `12345`
   - port: `5432`

## Adımlar

```bash
# Sanal ortam oluştur
python -m venv venv
# Aktifleştir
# .\venv\Scripts\activate
source venv/bin/activate
source .\venv\Scripts\activate

# Kütüphaneleri yükle
pip install -r requirements.txt

# Uygulamayı başlat
cd backend
uvicorn app.main:app --reload

sudo systemctl start postgresql
sudo -u postgres psql -d restaurant
