# ScrAioStudizba

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Async](https://img.shields.io/badge/Async-Aiohttp-informational)
![Scraper](https://img.shields.io/badge/Type-Scraper-green)
![Tooling](https://img.shields.io/badge/Tool-uv-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

🧠 An asynchronous web scraper for collecting university teacher profiles from [studizba.com](https://studizba.com), exporting them to Excel and organizing photos in a structured format.

Originally built as a freelance project to deliver a full dataset to a client. Now restructured for portfolio demonstration and public reference.

---

## 🔄 Features

+ Async scraping with rotating proxies
+ Parses universities, departments, and teacher profiles
+ Collects:
  - Department name
  - Teacher full name
  - HTML & plain-text description
  - External profile links
  - Profile photo(s)
+ Saves each institution's data to a separate styled `.xlsx` file
+ Stores teacher photos in subfolders
+ Archives results as `data.zip`
+ Logs progress and errors to `parser.log`

---

## 🏗 Output Structure

Each university creates a folder inside `data/`, like so:

```

data/
├── МГУ им. Ломоносова/
│   ├── name-url.txt
│   ├── teachers/
│   │   ├── Ivanov\_Ivan\_1.jpg
│   └── МГУ им. Ломоносова.xlsx
├── Финансовый университет/
│   ├── ...
└── institutions_urls.txt

````

- `name-url.txt` — one line: `<institution_name>*<url>`
- `institutions_urls.txt` — list of all institutions and their URLs

📷 Photos are saved in `teachers/`  
📊 Excel files contain structured rows per teacher:
- Department name
- Full name
- Description (HTML)
- Description (Text)
- Links
- Photo paths

---

## 🔧 Tech Stack

- Python 3.13+
- `uv` for virtual environment and dependency management
- `aiohttp` + `aiohttp-proxy`
- `beautifulsoup4`, `httplib2`, `tqdm`
- `openpyxl`, `transliterate`, `python-dotenv`

---

## ⚙️ Setup

```bash
   # Clone the project
   git clone https://github.com/yourname/ScrAioStudizba.git
   cd ScrAioStudizba
   
   # Create environment and install dependencies
   uv venv
   .venv/Scripts/activate  # or . .venv/bin/activate on Unix
   uv pip install -r requirements.txt
````

---

## 📚 .env configuration

Create a `.env` file with the following:

```dotenv
   PROXIES=https://user:pass@proxy1:port,https://user:pass@proxy2:port
   USER_AGENT="Mozilla/5.0 ..."
   TEACHERS_URL=https://studizba.com/teachers/
```

A template is available as `.env.example`.

---

## 🚀 Run

```bash
   python code/main.py
```

The parser will:

1. Collect all institution URLs
2. For each institution, parse departments and teachers
3. Save results in `data/`, then zip to `data.zip` and delete the folder

---

## 🎯 Use Case

Originally developed as a freelance order to deliver a complete dataset of teacher profiles across Russian universities from studizba.com.
Now redesigned and repackaged as a complete portfolio-ready async scraping solution.

---

## 📁 Screenshots

### Folder Structure

![Folder Tree](assets/folder1.png)
![Folder Tree](assets/folder2.png)
![Folder Tree](assets/folder3.png)
**name-url.txt**\
![Folder Tree](assets/folder4.png)\
**institutions_urls.txt**\
![Folder Tree](assets/folder5.png)


### Excel Output

![Excel Example](assets/excel.png)

---

## 📝 License

MIT License. See [LICENSE](./LICENSE) for more information.

---

**Author:** [XEQU](https://github.com/XEQU4)
