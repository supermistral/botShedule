from dotenv import load_dotenv
import os, datetime

load_dotenv()

# Токен в вк
TOKEN = os.environ.get("TOKEN")

# Токен для погоды
TOKEN_WEATHER = os.environ.get("TOKEN_WEATHER")

# Институты, которые нужно выгрузить в память
# ИИТ | ФТИ | ИРТС | КБИСП | ИТХТ | ИК | ИЭП | ИИНТЕГУ
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

# Дата старта учебы - день начала 1 учебной недели
# Формат - год, месяц, день
STUDY_FIRST_DAY = datetime.datetime(2021, 2, 9)

# Длительность семестра в неделях
STUDY_DURATION_WEEK = 17

# Недели которые заменены другими неделями
WEEKS_REPLACED = {
    17: 13,
}

# Имя базы данных
DB_NAME = "users.sqlite"

# Имя таблицы в бд
DB_TABLE_NAME = "users"
