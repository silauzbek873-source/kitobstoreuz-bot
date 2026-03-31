# KitobStoreUz Telegram bot

Bu bot quyidagilarni qiladi:
- kitob katalogini ko'rsatadi
- narxlarni chiqaradi
- buyurtma yig'adi
- buyurtmani admin'ga yuboradi
- muhokama guruhidagi sotuvga yaqin xabarlarni admin'ga alohida yuboradi
- foydalanuvchi savolini admin'ga forward qiladi

## 1. O'rnatish

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Sozlash

`.env.example` dagi qiymatlarni o'zingiznikiga moslang va environment ga kiriting.

Linux/macOS:

```bash
export BOT_TOKEN='TOKEN'
export ADMIN_USERNAME='abdullayevv_tm'
export ADMIN_USER_ID='123456789'
```

Windows PowerShell:

```powershell
$env:BOT_TOKEN='TOKEN'
$env:ADMIN_USERNAME='abdullayevv_tm'
$env:ADMIN_USER_ID='123456789'
```

## 3. Ishga tushirish

```bash
python main.py
```

## 4. Admin ulash

1. Botni ishga tushiring.
2. Admin akkauntdan botga `/start` yoki `/admin` yozing.
3. Shunda bot admin chat ID ni saqlaydi.

## 5. Muhokama guruhiga ulash

1. Botni guruhga qo'shing.
2. Admin qiling.
3. BotFather ichida bot uchun Privacy Mode ni o'chiring, aks holda barcha group xabarlarini ko'rmaydi.

## 6. Kitob qo'shish

`books.json` ichiga yangi kitoblarni shu formatda qo'shing:

```json
{
  "id": 4,
  "title": "Ikki eshik orasi",
  "price": 55000,
  "description": "Qisqa tavsif"
}
```

## 7. Keyin qo'shish mumkin bo'lgan funksiyalar

- to'lov tizimi
- admin panel ichidan kitob qo'shish
- statistika
- promo kodlar
- reklama yuborish
- Excel export
