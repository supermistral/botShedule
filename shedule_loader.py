import json, requests, os, openpyxl, re
from bs4 import BeautifulSoup as BS
import settings
from utils import FileUtils
from abc import abstractmethod


class SheduleLoader:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'}
        self.url = "https://www.mirea.ru/schedule/"

    
    def get_xlsxName(self, name: str) -> str:
        return FileUtils.get_path_xlsx(name + ".xlsx")


    def get_jsonName(self, name: str) -> str:
        return FileUtils.get_path_json(name + ".json")


    def get_shedule_refs(self) -> list:
        response = requests.get(self.url, headers=self.headers)
        bs = BS(response.text, 'lxml')
        block = bs.find("div", attrs={"class": "uk-clearfix"})

        search_table = lambda href: href and href.endswith(".xlsx")

        # All refs with .xls or .xlsx
        refList = block.find_all("a", href=search_table)
        refs = [ref.get("href") for ref in refList]

        if not refs:
            raise ValueError("References are not found")

        return refs


    def save_in_xlsx(self, ref: str, fileName: str) -> None:
        print(f"Запись -> {fileName + '.xlsx':45}", end="\t")
        open(self.get_xlsxName(fileName), 'wb').write(ref)
        print("успешно")


    def write_shedules(self, refList: list, fileNameList: list) -> None:
        for (ref, name) in zip(refList, fileNameList):
            self.save_in_xlsx(ref, name)


    def translate_to_json(self, fileNameList: list) -> None:
        for name in fileNameList:
            wb = openpyxl.load_workbook(self.get_xlsxName(name))
            sheet = wb[wb.sheetnames[0]]
            
            parser = SheduleParserExam(sheet) if re.search(r"(экз|сессия)", name.lower()) \
                else SheduleParserDefault(sheet)

            sheduleDict = parser.parse()
            
            self.save_in_json(sheduleDict, name)


    def parse_shedule(self) -> None:
        refs = self.get_shedule_refs()
        refsFiles = [requests.get(ref, headers=self.headers).content for ref in refs]

        if not refsFiles:
            raise ValueError("Web service are not available")

        fileNames = [re.search(r"(\w|[а-яА-Я]|-|\s|\.|\(|\)|,)+.xlsx$", ref).group(0) for ref in refs]
        fileNames = [re.sub(r"(\s|,|\)|\()", "_", name).replace("..", ".").replace(".xlsx", "") for name in fileNames]

        # Запись файлов
        FileUtils.remove_files_from_dir(settings.XLSX_DIR, ".xlsx")
        self.write_shedules(refsFiles, fileNames)

        # Открытие и парсинг файлов
        FileUtils.remove_files_from_dir(settings.JSON_DIR, ".json")
        self.translate_to_json(fileNames)


    def save_in_json(self, shedule: dict, fileName: str) -> None:
        print(f"Запись отформатированных данных -> {fileName + '.json':45}", end="\t")
        with open(self.get_jsonName(fileName), 'w', encoding="utf-8") as jsonFile:
            json.dump(
                shedule, 
                jsonFile, 
                ensure_ascii=False, 
                indent=2, 
                separators=(',', ': ')
            )
        if shedule:
            print("успешно")
        else:
            print("файл пуст!")



class SheduleParser:
    def __init__(self, table, offset, addOffset, startColIndex):
        """
        table - лист с расписанием
        offset - смещение по столбцам для поиска групп
        addOffset - добавочное смещение по столбцам при встрече с желтыми колонками
        startColIndex - индекс (буква) в столбце - индекс первой группы
        """
        self.table = table
        self.colIndex = startColIndex
        self.colIndexList = [startColIndex]
        self._colIndexOffset = offset
        self._colIndexAddOffset = addOffset


    def _update_colIndex(self, offset, ind, colIndexList) -> None:
        if ind < 0:
            colIndexList.insert(0, 'A')
            for i in range(1, len(colIndexList) - 1):
                colIndexList[i] = 'A'
            return

        temp = ord(colIndexList[ind]) + offset
        if temp > ord('Z'):
            t = ord('Z') - ord(colIndexList[ind])
            colIndexList[ind] = chr(ord('A') + offset - t - 1)
            self._update_colIndex(1, ind - 1, colIndexList)
        else:
            colIndexList[ind] = chr(temp)


    def update_colIndex(self, offset = None) -> str:
        offset = self._colIndexAddOffset if offset else self._colIndexOffset
        self._update_colIndex(offset, len(self.colIndexList) - 1, self.colIndexList)
        return "".join(self.colIndexList)


    def get_cell(self, ind, offset = 0) -> str:
        colList = self.colIndexList[::]
        self._update_colIndex(offset, len(colList) - 1, colList)
        return "".join(colList) + str(ind)


    @abstractmethod
    def colIndexSubject(self, i) -> str:
        return


    @abstractmethod
    def colIndexTypeSubject(self, i) -> str:
        return


    @abstractmethod
    def colIndexTeacher(self, i) -> str:
        return


    @abstractmethod
    def colIndexRoom(self, i) -> str:
        return

    
    def get_group_number(self) -> str:
        number = self.table[self.get_cell(2)].value

        # Встретилась запись, отличная от шаблона группы
        # - пустой столбец (в начале) или желтая колонка 'День недели'
        # Нужно прибавить отступ в self.colIndexOffset столбцов
        if number is None or not re.search(r"^[а-яА-Я]+-\d{2}-\d{2}$", number):
            self.colIndex = self.update_colIndex(self._colIndexAddOffset)

        return self.table[self.get_cell(2)].value


    def get_subjects(self, i) -> str:
        return self.table[self.colIndexSubject(i)].value


    def get_type_subjects(self, i) -> str:
        return self.table[self.colIndexTypeSubject(i)].value


    def get_teachers(self, i) -> str:
        return self.table[self.colIndexTeacher(i)].value


    def get_room(self, i) -> str:
        return self.table[self.colIndexRoom(i)].value


    def parse(self, start, end, weekLength, studyWeekLength, stepDay) -> dict:
        """
        Парсинг раписания и возврат в форме словаря: ключ - номер группы

        start - начальный индекс в строке
        end - конечный индекс в строке
        weekLength - количество строк в таблице под 1 неделю
        studyWeekLength - количество строк в таблице под 1 неделю с реальными значениями
        stepDay - шаг внутри недели для парсинга каждого дня
        """

        shedule = {}

        while (1):
            # Конец таблицы - 2 пустых ячейки с номером группы подряд
            # Проверка на пустую колонку, за которой есть информация (не конец таблицы)
            # Защита от неверно составленного расписания с пропущенной колонкой
            group = self.get_group_number()
            if not group or not re.compile(r"[а-яА-Я]+-\d{2}-\d{2}").search(group):
                group = self.get_group_number()
                if not group or not re.compile(r"[а-яА-Я]+-\d{2}-\d{2}").search(group):
                    break

            shedule.update(self.parse_group(start, end, weekLength, studyWeekLength, stepDay))
            self.colIndex = self.update_colIndex()

        return shedule


    def parse_group(self, start, end, weekLength, studyWeekLength, stepDay) -> dict:
        group = {}

        numberGroup = self.get_group_number()
        group[numberGroup] = self.get_group_number()
        group[numberGroup] = []

        for rowIndex in range(start, end, weekLength):
            group[numberGroup].append([])
            for tempRowIndex in range(rowIndex, rowIndex + studyWeekLength, stepDay):
                group[numberGroup][-1].append(self.get_row_data(tempRowIndex))

        return group


    @abstractmethod
    def get_row_data(self, rowIndex) -> dict or None:
        """
        Получение информации о занятии по индексу в строке таблицы
        """
        return



class SheduleParserDefault(SheduleParser):
    def __init__(self, table):
        super().__init__(table, 5, 5, 'F')

    
    def colIndexSubject(self, i) -> str:
        return self.get_cell(i)


    def colIndexTypeSubject(self, i) -> str:
        return self.get_cell(i, 1)


    def colIndexTeacher(self, i) -> str:
        return self.get_cell(i, 2)


    def colIndexRoom(self, i) -> str:
        return self.get_cell(i, 3)


    def parse(self) -> dict:
        return super().parse(4, 76, 12, 12, 1)


    def get_row_data(self, rowIndex) -> dict or None:
        row = {}
        row["pair"] = self.get_subjects(rowIndex)

        if row["pair"] is None or not re.compile(r"[а-яА-Я]+").search(row["pair"]):
            return None

        row["type"] = self.get_type_subjects(rowIndex)
        row["teacher"] = self.get_teachers(rowIndex)
        row["room"] = self.get_room(rowIndex)
    
        return row



class SheduleParserExam(SheduleParser):
    def __init__(self, table):
        super().__init__(table, 4, 2, 'C')

    
    def colIndexSubject(self, i) -> str:
        return self.get_cell(i + 1)


    def colIndexTypeSubject(self, i) -> str:
        return self.get_cell(i)


    def colIndexTeacher(self, i) -> str:
        return self.get_cell(i + 2)


    def colIndexRoom(self, i) -> str:
        return self.get_cell(i, 2)


    def colIndexTime(self, i) -> str:
        return self.get_cell(i, 1)
    

    def get_time(self, i) -> str:
        return self.table[self.colIndexTime(i)].value


    def parse(self) -> dict:
        return super().parse(3, 60, 19, 18, 3)


    def get_row_data(self, rowIndex) -> dict or None:
        row = {}
        row["pair"] = self.get_subjects(rowIndex)

        if row["pair"] is None or not re.compile(r"[а-яА-Я]+").search(row["pair"]):
            return None

        row["type"] = self.get_type_subjects(rowIndex)
        row["teacher"] = self.get_teachers(rowIndex)
        row["time"] = self.get_time(rowIndex)
        row["room"] = self.get_room(rowIndex)
    
        return row



if __name__ == "__main__":
    loader = SheduleLoader()
    loader.parse_shedule()