import os, re, settings, json, datetime
from utils import FileUtils


class SheduleReader:
    def __init__(self):
        self.shedule = {"default": {}, "test": {}, "exam": {}}
        self.sheduleTeacher = {}        # расписание преподавателей
        self.read_json()
        self.months = [
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа',
            'сентября', 'октября', 'ноября', 'декабря' 
        ]


    def read_json(self) -> None:
        """
        Чтение файла json выбранных институтов -> загрузка в память
        """

        institutions = settings.INSTITUTIONS

        reExp = None
        if isinstance(institutions, str) and institutions == "__all__":
            reExp = re.compile(r"^.*$")
        elif isinstance(institutions, (list, tuple)):
            pattern = r"(" + r"|".join([name.lower() for name in institutions]) + r")"
            reExp = re.compile(pattern)
        else:
            raise TypeError("Unreadable setting - INSTITUTIONS")
        
        fileList = os.listdir(settings.JSON_DIR)
        fileList = list(filter(lambda name: reExp.search(name.lower()), fileList))

        if not fileList:
            raise ValueError("Nothing to read")

        fileList = [FileUtils.get_path_json(name) for name in fileList]
        
        for fileName in fileList:
            with open(fileName, 'r', encoding="utf-8") as f:
                sheduleDict = json.load(f)
                key = "default"
                if "зач" in fileName.lower():
                    key = "test"
                elif "экз" in fileName.lower() or "сессия" in fileName.lower():
                    key = "exam"

                self.shedule[key].update(sheduleDict)


    def get_group_shedule(self, group, date=datetime.datetime.today(), date_last=None) -> str:
        """
        Получение расписание группы по дате

        Дата может быть единственным значением datetime.datetime

        Если передается date_last, то date означает начало
            а date_last - конец промежутка, по которому требуется получить данные
        """

        message = ""
        dates = []

        if date_last is None:
            dates.append(date)
        else:
            tempData = date
            while (tempData <= date_last):
                dates.append(tempData)
                tempData += datetime.timedelta(days=1)

        for oneDate in dates:
            studyWeek = self.get_week(oneDate)

            if studyWeek > settings.STUDY_DURATION_WEEK:
                message += self.get_group_shedule_exam(group, date)
                break
            
            message += f"Расписание на {oneDate.day} {self.months[oneDate.month]}\n"
            # Проверка на замененные недели
            if studyWeek in settings.WEEKS_REPLACED:
                studyWeek = settings.WEEKS_REPLACED[studyWeek]
            shedule = self.get_group_day_shedule(group, oneDate, studyWeek)

            if shedule is None:
                message = "не найдено"
                break
            message += self.format_group_day_shedule(shedule, studyWeek) + "\n"

        return message

    
    def get_group_day_shedule(self, group, date, week) -> list or None:
        """
        Получение раписания (списка пар) по группе и дню
        """

        key = "default"
        if week == settings.STUDY_DURATION_WEEK + 1:
            key = "test"

        if group not in self.shedule[key] or date.weekday() > 5:
            return None

        return self.shedule[key][group][date.weekday()]


    def format_group_day_shedule(self, shedule, week) -> str:
        """
        Форматирование строки с списком пар по выбранной неделе

        Содержит логику итерации по списку пар (12 элементов)

        Определяет четность/нечетность недели
        """

        isEven = True
        if week % 2 == 1:
            isEven = False

        stringShedule = ""

        for ind in range(isEven, 12, 2):
            stringShedule += str((ind + 2) // 2) + ") "

            if shedule[ind] is None:
                stringShedule += "-\n"
            else:
                stringShedule += self.format_pair(shedule[ind], week)

        return stringShedule


    def format_pair(self, pair, week) -> str:
        """
        Форматирование элемента списка с расписанием

        Возвращает строку с парой, типом занятия и т.д.
        """

        pairs       = self.check_pairUnit(pair["pair"])
        typesPairs  = self.check_pairUnit(pair["type"])
        teachers    = self.check_pairUnit(pair["teacher"])
        rooms       = self.check_pairUnit(pair["room"])
        formatPair  = ""

        for ind in range(len(pairs)):
            pairString = pairs[ind]

            # Поиск строки 'кр.' - 'кроме' недели (на этой неделе пары нет)
            weekExceptionReg = re.compile(r"кр\.?\s\(\d+,?\s?)+ н\.?\s?").search(pairString.lower())
            if weekExceptionReg:
                tempWeeksString = weekExceptionReg.group(0)
                if str(week) in tempWeeksString.split(" ")[1].split(","):
                    continue
                formatPair += tempWeeksString.replace(tempWeeksString, "")

            # Поиск строки '1, 2, 3, 4 н.' - недели, на которых проходят пары
            weekNoExceptionReg = re.compile(r"(\d+,?\s?)+ н\.?\s?").search(pairString.lower())
            if weekNoExceptionReg:
                tempWeeksString = weekNoExceptionReg.group(0)
                if str(week) not in tempWeeksString.split(" ")[0].split(","):
                    continue
                formatPair += pairString.replace(tempWeeksString, "")
            else:
                formatPair += pairString

            formatPair += f" | {self.get_pairUnit(typesPairs, ind)} | {self.get_pairUnit(teachers, ind)}" + \
                f" | {self.get_pairUnit(rooms, ind)}\n"

        if not formatPair:
            return "-\n"
        return formatPair

    
    def get_pairUnit(self, stringList, ind) -> str:
        if ind >= len(stringList):
            return "-"
        return stringList[ind]


    def check_pairUnit(self, pairUnit) -> list:
        if pairUnit is None:
            return []
        return pairUnit.split("\n")

    
    def get_week(self, date=datetime.datetime.today()) -> int:
        return (date - settings.STUDY_FIRST_DAY).days // 7 + 1

    
    def get_group_shedule_exam(
        self, 
        group: str, 
        date: datetime.datetime = datetime.datetime.today(), 
        date_last: datetime.datetime or None = None
    ) -> str:
        """
        Получение расписание экзаменов группы по дате

        Дата может быть единственным значением datetime.datetime

        Если date_last не передается, то выдается информация по раписанию текущей недели
        
        Если передается date_last, то date означает начало
            а date_last - конец промежутка, по которому требуется получить данные
        """

        message = ""
        dates = []
        dateFirstExam = settings.STUDY_FIRST_DAY + datetime.timedelta(weeks=settings.STUDY_DURATION_WEEK + 1)
        dateFirstExam = dateFirstExam - datetime.timedelta(days=dateFirstExam.weekday())
        daysFromFirstDate = (date - dateFirstExam).days
        index = daysFromFirstDate - daysFromFirstDate // 7

        if (index // 6) + 1 > len(self.shedule["exam"][group]):
            return "Раписания нет"

        if date_last is None:
            date_last = date + datetime.timedelta(days=5-date.weekday())

        tempData = date
        while (tempData <= date_last):
            if tempData.weekday() != 6:         # Кроме воскресений
                dates.append(tempData)
            tempData += datetime.timedelta(days=1)

        for oneDate in dates:
            if oneDate == settings.LAST_DAY_EXAM:
                message += f"{oneDate.day} {self.months[oneDate.month]} - день пересдач"
                break

            pair = self.shedule["exam"][group][index // 6][index % 6]
            index += 1

            if pair is None:
                continue
            
            message += f"Расписание на {oneDate.day} {self.months[oneDate.month]}\n"
            message += self.format_pair_exam(pair) + "\n"

        return message


    def format_pair_exam(self, pair: dict) -> str:
        pairName    = pair["pair"]
        typePair    = pair["type"]
        teacher     = self.get_pairUnit_exam(pair["teacher"])
        time        = self.get_pairUnit_exam(pair["time"])
        room        = self.get_pairUnit_exam(pair["room"])

        formatPair  = f"{typePair.upper()} -> {pairName} | {teacher} | {time} | {room}\n"
        return formatPair


    def get_pairUnit_exam(self, pairUnit: str or None) -> str:
        if pairUnit is None:
            return "-"
        return pairUnit



if __name__ == "__main__":
    reader = SheduleReader()
    # print(reader.get_group_shedule_exam("ИКБО-01-20"))