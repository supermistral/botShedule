import vk_api, re, settings, json, datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from shedule_reader import SheduleReader
from utils import InteractionSQL


class VK:
    def __init__(self, token):
        self.vk_sess        = vk_api.VkApi(token=token)
        self.vk             = self.vk_sess.get_api()
        self.longpoll       = VkLongPoll(self.vk_sess)
        self.keyboards      = self.generate_keyboards()
        self.curKeyboard    = None
        self.groupRegExp    = re.compile(r"^[А-Я]+-\d{2}-\d{2}$")
        self.reader         = SheduleReader()
        self.sql            = InteractionSQL()

    
    def generate_keyboards(self) -> dict:
        keyboards = {}
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button("На сегодня", color=VkKeyboardColor.POSITIVE, payload={"command": "shedule_today"})
        keyboard.add_button("На завтра", color=VkKeyboardColor.NEGATIVE, payload={"command": "shedule_tomorrow"})
        keyboard.add_line()
        keyboard.add_button("на эту неделю", color=VkKeyboardColor.PRIMARY, payload={"command": "shedule_week_current"})
        keyboard.add_button("на следующую неделю", color=VkKeyboardColor.PRIMARY, payload={"command": "shedule_week_next"})
        keyboard.add_line()
        keyboard.add_button("какая неделя?", color=VkKeyboardColor.SECONDARY, payload={"command": "shedule_week"})
        keyboard.add_button("какая группа?", color=VkKeyboardColor.SECONDARY, payload={"command": "shedule_group"})
        keyboards["shedule"] = keyboard

        return keyboards
    

    def run(self) -> None:
        for event in self.longpoll.listen():

            if event.type == VkEventType.MESSAGE_NEW and \
                event.text and event.to_me and event.from_user:

                if "payload" in event.raw[6]:
                    payload = json.loads(event.raw[6]["payload"])
                    msg = self.handle_keyboard(event.user_id, payload)
                else:
                    msg = self.handle_message(event.user_id, event.text)

                self.msg(event.user_id, msg, keyboard=self.curKeyboard)
                self.curKeyboard = None
    

    def msg(self, user_id, message, **kwargs) -> None:
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(), 
            message=message,
            **kwargs
        )


    def handle_message(self, userId, message) -> str:
        message = message.lower()
        
        if self.groupRegExp.search(message.upper()):
            self.sql.update_group(userId, message.upper())
            return f"Вы установили группу {message.upper()}"

        elif message == "бот":
            self.curKeyboard = self.keyboards["shedule"].get_keyboard()
            return "Выберете дату"

        elif message == "начать":
            self.sql.first_interaction(userId)
            return (
                """
                ИНСТРУКЦИЯ ДЛЯ БОТА:
                SSSS-II-II -> установить группу для показа раписания
                Бот -> Меню для раписания
                """
            )

        else:
            return "Неизвестная команда"
    

    def handle_keyboard(self, userId, payload) -> str:
        if "command" not in payload:
            return "Неизвестная команда"

        textPayload = payload["command"]

        if "shedule" in textPayload:
            group = self.sql.get_group(userId)

            if not group:
                return "Группа не установлена"

            if textPayload == "shedule_today":
                return self.reader.get_group_shedule(group)
            elif textPayload == "shedule_tomorrow":
                return self.reader.get_group_shedule(
                    group, 
                    datetime.datetime.today() + datetime.timedelta(days=1)
                )
            elif textPayload == "shedule_week_current":
                dateToday = datetime.datetime.today()
                dateStart = dateToday - datetime.timedelta(days=dateToday.weekday())
                return self.reader.get_group_shedule(
                    group,
                    dateStart,
                    dateStart + datetime.timedelta(days=5)
                )
            elif textPayload == "shedule_week_next":
                dateToday = datetime.datetime.today()
                dateStart = dateToday + datetime.timedelta(days=7-dateToday.weekday())
                return self.reader.get_group_shedule(
                    group,
                    dateStart,
                    dateStart + datetime.timedelta(days=5)
                )
            elif textPayload == "shedule_week":
                return f"Идет {self.reader.get_week()} неделя"
            elif textPayload == "shedule_group":
                return f"Установлена группа {group}"

        return "Неизвестная команда"



if __name__ == "__main__":
    vk = VK(settings.TOKEN)
    vk.run()