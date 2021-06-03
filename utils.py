import settings, os, sqlite3


class FileUtils:

    @staticmethod
    def get_path_xlsx(name) -> str:
        """
        Получение пути к файлу из директории xlsx-таблиц
        """
        return os.path.join(settings.XLSX_DIR, name)

    @staticmethod
    def get_path_json(name) -> str:
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

    
    def create_connection(self):
        self.conn = sqlite3.connect(self.dbName, check_same_thread=False)
        self.cur = self.conn.cursor()


    def create_table(self):
        self.cur.execute("CREATE TABLE IF NOT EXISTS ? (user_id TEXT, group TEXT)", self.tableName)
        self.conn.commit()


    def create_user(self, userId):
        self.cur.execute("INSERT INTO ? (user_id) VALUES ?", (self.tableName, userId))
        self.conn.commit()

    
    def update_group_user(self, userId, group):
        self.cur.execute("UPDATE ? SET group = ? WHERE user_id = ?", (self.tableName, group, userId))
        self.conn.commit()




class InteractionSQL:
    def __init__(self):
        pass