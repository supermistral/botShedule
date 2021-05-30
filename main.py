import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import settings


class VK:
    def __init__(self, token) -> None:
        self.vk_sess = vk_api.VkApi(token=token)
        self.vk = self.vk_sess.get_api()
        self.longpoll = VkLongPoll(self.vk_sess)
    
    def run(self):
        for event in self.longpoll.listen():
            print(event)

            if event.type == VkEventType.MESSAGE_NEW and \
                event.text and event.to_me and event.from_user:
                pass
    
    def msg(self, user_id, message):
        self.vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message)


if __name__ == "__main__":
    vk = VK(settings.TOKEN)
    vk.run()