from dotenv import load_dotenv
import os

load_dotenv()

# Токен в вк
TOKEN = os.environ.get("TOKEN")

# Институты, которые нужно выгрузить в память
# ИИТ | ФТИ | ИРТС | КБИСП | ИТХТ | ИКИБ | ИЭП | ИИНТЕГУ
# Пример : INSTITUTIONS = ['ИИТ']
INSTITUTIONS = ["ИИТ"]

# Базовая директория
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Директория с файлами расписания
SHEDULE_DIR = os.path.join(BASE_DIR, "shedule")

# Директория с таблицами xlsx
XLSX_DIR = os.path.join(SHEDULE_DIR, "xlsx")

# Директория с json
JSON_DIR = os.path.join(SHEDULE_DIR, "json")
