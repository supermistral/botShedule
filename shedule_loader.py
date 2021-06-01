import json, requests, os, openpyxl, re
from bs4 import BeautifulSoup as BS
import settings
from utils import FileUtils


class SheduleLoader:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0'}
        self.url = "https://www.mirea.ru/schedule/"

    
    def get_xlsxName(self, name) -> str:
        return FileUtils.get_path_xlsx(name + ".xlsx")


    def get_jsonName(self, name) -> str:
        return FileUtils.get_path_json(name + ".json")


    def get_shedule_refs(self) -> list:
        response = requests.get(self.url, headers=self.headers)
        bs = BS(response.text, 'lxml')
        block = bs.find("div", attrs={"class": "uk-clearfix"})

        search_table = lambda href: href and re.compile(r"\.xlsx$").search(href)

        # All refs with .xls or .xlsx
        refList = block.find_all("a", href=search_table)
        refs = [ref.get("href") for ref in refList]

        if not refs:
            raise ValueError("References are not found")

        return refs


    def save_in_xlsx(self, ref, fileName) -> None:
        print(f"Запись -> {fileName}.xlsx", end="\t")
        open(self.get_xlsxName(fileName), 'wb').write(ref)
        print("успешно")


    def write_shedules(self, refList, fileNameList) -> None:
        for (ref, name) in zip(refList, fileNameList):
            self.save_in_xlsx(ref, name)


    def translate_to_json(self, fileNameList) -> None:
        for name in fileNameList:
            wb = openpyxl.load_workbook(self.get_xlsxName(name))
            sheet = wb[wb.sheetnames[0]]
            
            parser = SheduleParser(sheet)
            sheduleList = parser.parse()
            
            self.save_in_json(sheduleList, name)


    def parse_shedule(self) -> None:
        refs = self.get_shedule_refs()
        refsFiles = [requests.get(ref, headers=self.headers).content for ref in refs]

        if not refsFiles:
            raise ValueError("Web service are not available")

        fileNames = [re.search(r"(\w|[а-яА-Я]|-|\s|\.|\(|\)|,)+.xlsx$", ref).group(0) for ref in refs]
        fileNames = [re.sub(r"(\s|,|\)|\()", "_", name).replace("..", ".").replace(".xlsx", "") for name in fileNames]

        # Запись файлов
        self.write_shedules(refsFiles, fileNames)

        # Открытие и парсинг файлов
        self.translate_to_json(fileNames)


    def save_in_json(self, shedule, fileName) -> None:
        print(f"Запись отформатированных данных -> {fileName}.json", end="\t")
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
    def __init__(self, table):
        self.table = table
        self.colIndex = 'F'
        self.colIndexList = ['F']


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


    def update_colIndex(self) -> str:
        self._update_colIndex(5, len(self.colIndexList) - 1, self.colIndexList)
        return "".join(self.colIndexList)


    def get_cell(self, ind, offset = 0) -> str:
        colList = self.colIndexList[::]
        self._update_colIndex(offset, len(colList) - 1, colList)
        return "".join(colList) + str(ind)


    def colIndexSubject(self, i) -> str:
        return self.get_cell(i)


    def colIndexTypeSubject(self, i) -> str:
        return self.get_cell(i, 1)


    def colIndexTeacher(self, i) -> str:
        return self.get_cell(i, 2)


    def colIndexRoom(self, i) -> str:
        return self.get_cell(i, 3)


    def get_group_number(self) -> str:
        number = self.table[self.get_cell(2)].value

        # Встретилась запись, отличная от шаблона группы
        # - пустой столбец (в начале) или желтая колонка 'День недели'
        # Нужно прибавить отступ в 5 столбцов
        if number is None or not re.compile(r"[а-яА-Я]+-\d+").search(number):
            self.colIndex = self.update_colIndex()

        return self.table[self.get_cell(2)].value


    def get_subjects(self, i) -> str:
        return self.table[self.colIndexSubject(i)].value


    def get_type_subjects(self, i) -> str:
        return self.table[self.colIndexTypeSubject(i)].value


    def get_teachers(self, i) -> str:
        return self.table[self.colIndexTeacher(i)].value


    def get_room(self, i) -> str:
        return self.table[self.colIndexRoom(i)].value


    def parse(self) -> list:
        shedule = []

        while (1):
            # Конец таблицы - пустая ячейка
            if not self.get_group_number() \
                or not self.get_group_number().replace(" ", ""):
                break

            shedule.append(self.parse_group())
            self.colIndex = self.update_colIndex()

        return shedule


    def parse_group(self) -> dict:
        group = {}

        numberGroup = self.get_group_number()
        group[numberGroup] = self.get_group_number()
        group[numberGroup] = []

        for rowIndex in range(4, 76, 12):
            group[numberGroup].append([])
            for tempRowIndex in range(rowIndex, rowIndex + 12):
                group[numberGroup][-1].append(self.get_row_data(tempRowIndex))

        return group


    def get_row_data(self, rowIndex) -> dict or None:
        row = {}
        row["pair"] = self.get_subjects(rowIndex)

        if row["pair"] is None or not re.compile(r"[а-яА-Я]+").search(row["pair"]):
            return None

        row["type"] = self.get_type_subjects(rowIndex)
        row["teacher"] = self.get_teachers(rowIndex)
        row["room"] = self.get_room(rowIndex)
    
        return row



if __name__ == "__main__":
    loader = SheduleLoader()
    loader.parse_shedule()