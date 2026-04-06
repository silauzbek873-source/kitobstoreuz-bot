function buyBook(bookName) {
  const botUsername = "sizning_bot_username";
  const url = `https://t.me/${botUsername}?start=${encodeURIComponent("book_" + bookName)}`;
  window.open(url, "_blank");
}
