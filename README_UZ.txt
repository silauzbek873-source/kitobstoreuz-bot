KITOBSTOREUZ FINAL BOT

Bu faylda token va admin id tayyor qo'yilgan.
Ishga tushirish:
1) pip install -r requirements.txt
2) python bot.py

SAYTDAGI TUGMA UCHUN:
function buyBook(bookName) {
  const botUsername = "sizning_bot_username";
  const url = `https://t.me/${botUsername}?start=${encodeURIComponent("book_" + bookName)}`;
  window.open(url, "_blank");
}

MUHIM:
Agar GitHub ga joylasangiz, token ochiq ko'rinib qoladi.
Shuning uchun public GitHub ga shu holatda tashlamang.
