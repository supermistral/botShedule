import vk_api, re, settings
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from shedule_reader import SheduleReader


class VK:
    def __init__(self, token):
        self.vk_sess = vk_api.VkApi(token=token)
        self.vk = self.vk_sess.get_api()
        self.longpoll = VkLongPoll(self.vk_sess)
        self.keyboards = self.generate_keyboards()
        self.groupRegExp = re.compile(r"^[А-Я]-\d{2}-\d{2}$")
        self.reader = SheduleReader()

    
    def generate_keyboards(self) -> dict:
        keyboards = {}
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button("На сегодня", color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button("На завтра", color=VkKeyboardColor.NEGATIVE)
        keyboards["shedule"] = keyboard

        return keyboards
    

    def run(self) -> None:
        for event in self.longpoll.listen():
            print(event)

            if event.type == VkEventType.MESSAGE_NEW and \
                event.text and event.to_me and event.from_user:

                msg = self.parse_message(event.text)
                self.msg(event.user_id, msg)
    

    def msg(self, user_id, message, **kwargs) -> None:
        self.vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(), 
            message=message,
            **kwargs
        )


    def parse_message(self, message) -> str:
        if self.groupRegExp.search(message.uppper()):
            return self.reader.get_group_shedule(message.upper())
        else:
            return "Неизвестная команда"



if __name__ == "__main__":
    vk = VK(settings.TOKEN)
    vk.run()