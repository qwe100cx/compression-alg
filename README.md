Как запускать:
1. python -m http.server 8000
2. python proxy.py

Далее:
Откройте:
Оригинальная страница:
http://localhost:8000/test_page.html
Проксированная версия:
http://localhost:5000/proxy?url=http://localhost:8000/test_page.html
