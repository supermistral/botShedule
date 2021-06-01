import settings, os


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