import os, re, settings, json
from utils import FileUtils


class SheduleReader:
    def __init__(self):
        self.shedule = {}

    def read_json(self) -> None:
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
            print("Nothing to read")
            return

        fileList = [FileUtils.get_path_json(name) for name in fileList]
        
        for fileName in fileList:
            f = open(fileName, 'r', encoding="utf-8")
            sheduleList = json.load(f)
            for shedule in sheduleList:
                self.shedule.update(shedule)
            # print(type(json.load(f)) == list)
            # self.shedule.update(json.load(f))


if __name__ == "__main__":
    reader = SheduleReader()
    reader.read_json()
    print(reader.shedule)