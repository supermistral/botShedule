import settings, os, sqlite3


class FileUtils:

    @staticmethod
    def get_path_xlsx(name: str) -> str:
        """
        Получение пути к файлу из директории xlsx-таблиц
        """
        return os.path.join(settings.XLSX_DIR, name)

    @staticmethod
    def get_path_json(name: str) -> str:
        """
        Получение пути к файлу из директории json
        """
        return os.path.join(settings.JSON_DIR, name)



class SQL:
    def __init__(self):
        self.dbName = settings.DB_NAME
        self.tableName = settings.DB_TABLE_NAME
        self.conn = None
        self.cur = None

    
    def create_connection(self) -> None:
        self.conn = sqlite3.connect(self.dbName, check_same_thread=False)
        self.cur = self.conn.cursor()


    def create_table(self) -> None:
        self.cur.execute("CREATE TABLE IF NOT EXISTS %s (user_id TEXT, study_group TEXT)" %self.tableName)
        self.conn.commit()


    def create_user(self, userId: str) -> None:
        self.cur.execute("INSERT INTO %s (user_id) VALUES (?)" %self.tableName, (userId,))
        self.conn.commit()

    
    def update_group_user(self, userId: str, group: str) -> None:
        self.cur.execute("UPDATE %s SET study_group = ? WHERE user_id = ?" %self.tableName, (group, userId))
        self.conn.commit()

    
    def get_group_user(self, userId: str) -> str or None:
        group = self.cur.execute("SELECT study_group FROM %s WHERE user_id = ?" %self.tableName, (userId,)).fetchone()[0]
        return group



class InteractionSQL:
    def __init__(self):
        self.sql = SQL()
        self.sql.create_connection()
        self.sql.create_table()

    
    def first_interaction(self, userId: str) -> None:
        self.sql.create_user(userId)

    
    def update_group(self, userId: str, group: str) -> None:
        self.sql.update_group_user(userId, group)

    
    def get_group(self, userId: str) -> str:
        return self.sql.get_group_user(userId)