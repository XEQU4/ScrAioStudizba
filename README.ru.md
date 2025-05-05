# ScrAioStudizba

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Async](https://img.shields.io/badge/Async-Aiohttp-informational)
![Scraper](https://img.shields.io/badge/Type-Scraper-green)
![Tooling](https://img.shields.io/badge/Tool-uv-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

**📄 Этот README также доступен на [English](./README.md)**

🧠 Асинхронный веб-парсер преподавателей с сайта [studizba.com](https://studizba.com), сохраняющий данные по вузам, кафедрам и преподавателям в Excel и в виде фотографий.

Изначально был реализован как фриланс-заказ для выгрузки полной базы данных. Впоследствии перепакован для демонстрации на выставках и в портфолио.

---

## 🔄 Возможности

+ Асинхронный парсинг с ротацией прокси
+ Обход всех вузов, кафедр и преподавателей
+ Сбор информации:
  - Название кафедры
  - ФИО преподавателя
  - Описание (HTML и текст)
  - Ссылки на внешние профили
  - Фотографии преподавателя
+ Сохранение данных каждого вуза в отдельный Excel-файл
+ Хранение фотографий в подкаталогах
+ Автоматическое архивирование `data.zip`
+ Логирование в `parser.log`

---

## 🏗 Структура выходных данных

Каждый вуз создает свою папку в директории `data/`, например:

```

data/
├── МГУ им. Ломоносова/
│   ├── name-url.txt
│   ├── teachers/
│   │   ├── Ivanov\_Ivan\_1.jpg
│   └── МГУ им. Ломоносова.xlsx
├── Финансовый университет/
│   ├── ...
└── institutions\_urls.txt

````

- `name-url.txt` — строка формата `<название>*<url>`
- `institutions_urls.txt` — список всех вузов и их ссылок

📷 Фото сохраняются в `teachers/`  
📊 Excel-файл включает строки по каждому преподавателю:
- Кафедра
- ФИО
- Описание (HTML)
- Описание (TEXT)
- Ссылки
- Пути к фотографиям

---

## 🔧 Технологии

- Python 3.13+
- `uv` — управление окружением и зависимостями
- `aiohttp`, `aiohttp-proxy`
- `beautifulsoup4`, `httplib2`, `tqdm`
- `openpyxl`, `transliterate`, `python-dotenv`

---

## ⚙️ Установка

```bash
   # Клонируем проект
   git clone https://github.com/yourname/ScrAioStudizba.git
   cd ScrAioStudizba
   
   # Создаем окружение и устанавливаем зависимости
   uv venv
   .venv/Scripts/activate  # или . .venv/bin/activate для Unix
   uv pip install -r requirements.txt
````

---

## 📚 Настройка .env

Создайте `.env` файл с содержимым:

```dotenv
   PROXIES=https://user:pass@proxy1:port,https://user:pass@proxy2:port
   USER_AGENT="Mozilla/5.0 ..."
   TEACHERS_URL=https://studizba.com/teachers/
```

Пример доступен в `.env.example`.

---

## ▶️ Запуск

```bash
   python code/main.py
```

Парсер:

1. Собирает ссылки на все вузы
2. Для каждого вуза парсит кафедры и преподавателей
3. Сохраняет всё в `data/`, архивирует в `data.zip`, затем удаляет папку

---

## 🎯 Назначение

Проект был заказан для сбора публичных данных с сайта studizba.com. В текущем виде служит демонстрацией асинхронного парсинга и удобной организации данных в портфолио.

---

## 📁 Скриншоты

### Структура проекта

![Folder Tree](assets/folder1.png)
![Folder Tree](assets/folder2.png)
![Folder Tree](assets/folder3.png)
**name-url.txt**\
![Folder Tree](assets/folder4.png)\
**institutions\_urls.txt**\
![Folder Tree](assets/folder5.png)

### Excel-таблица

![Excel Example](assets/excel.png)

---

## 📝 Лицензия

Проект распространяется под лицензией MIT. Подробнее — см. [LICENSE](./LICENSE).

---

**Автор:** [XEQU](https://github.com/XEQU4)
