import vk_api
from random import randrange
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def write_msg(vk, user_id, message, list_city=None, num_keyboard=0):
    keyboard = VkKeyboard(one_time=False, inline=True)
    if num_keyboard == 1:
        for i, item in enumerate(list_city):
            info = f"{item[1][0]}{item[1][len(item[1]) - 1]}"
            text_button = (info[:37] + '...') if len(info) > 40 else info
            if i < (len(list_city)-1):
                keyboard.add_callback_button(text_button, VkKeyboardColor.POSITIVE, payload=f'{item[0]}')
                keyboard.add_line()
            else:
                keyboard.add_callback_button(text_button, VkKeyboardColor.POSITIVE, payload=f'{item[0]}')
        values = {
            'message': message,
            'user_id': user_id,
            'random_id': randrange(10 ** 7),
            'keyboard': keyboard.get_keyboard()
        }
    elif num_keyboard == 0:
        values = {
            'message': message,
            'user_id': user_id,
            'random_id': randrange(10 ** 7)
        }
    elif num_keyboard == 2:
        payload_data = ['100001', '100002']
        for i, item in enumerate(list_city):
            keyboard.add_callback_button(item, VkKeyboardColor.POSITIVE, payload=payload_data[i])
        values = {
            'message': message,
            'user_id': user_id,
            'random_id': randrange(10 ** 7),
            'keyboard': keyboard.get_keyboard()
        }
    else:
        values = {
            'message': message,
            'user_id': user_id,
            'random_id': randrange(10 ** 7),
            'keyboard': keyboard.get_empty_keyboard()
        }
    res = vk.method('messages.send', values=values)
    return res


def get_cities(token_user, text):
    vk_1 = vk_api.VkApi(token=token_user)
    values = {
        'country_id': 1,
        'q': text,
        'count': 4
    }
    try:
        res = vk_1.method('database.getCities', values=values)
        list_city = []
        for item in res['items']:
            str_city = []
            str_city.append(f" {item['title']}")
            if 'area' in item:
                str_city.append(f", {item['area']}")
            if 'region' in item:
                str_city.append(f", {item['region']}")
            list_city.append((item['id'], str_city))
        return list_city
    except Exception as ex:
        print(ex)
