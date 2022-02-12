import db_connect as db
import requests
import time
from random import randrange
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def write_result_msg(vk, user_id, message, content_source, attachment=None, num_keyboard=1, save_flag=False):
    keyboard = VkKeyboard(one_time=True, inline=False)
    if num_keyboard == 1:
        if save_flag:
            payload_data = ['303', '304']
            for i, item in enumerate(["Like", "Дальше"]):
                keyboard.add_callback_button(item, VkKeyboardColor.POSITIVE, payload=payload_data[i])
        else:
            payload_data = ['301', '302', '303', '304']
            for i, item in enumerate(["Black", "Save", "Like", "Дальше"]):
                keyboard.add_callback_button(item, VkKeyboardColor.POSITIVE, payload=payload_data[i])
        values = {
            'message': message,
            'user_id': user_id,
            'content_source': content_source,
            'attachment': attachment,
            'random_id': randrange(10 ** 7),
            'keyboard': keyboard.get_keyboard()
        }
    elif num_keyboard == 2:
        values = {
            'message': message,
            'user_id': user_id,
            'content_source': content_source,
            'attachment': attachment,
            'random_id': randrange(10 ** 7),
        }
    elif num_keyboard == 3:
        keyboard.add_callback_button("Дальше", VkKeyboardColor.POSITIVE, payload='304')
        values = {
            'message': message,
            'user_id': user_id,
            'content_source': content_source,
            'attachment': attachment,
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


def set_result_in_chat(vk, owner_id, token_user, list_in, save_flag):
    list_short_link = get_short_link(token_user, list_in)
    content_source = f'{{"type": "url", "url": "https://vk.com/id{list_in[0]}"}}'
    count = 0
    for photo_id in list_in[2]:
        count += 1
        if count == 1:
            message = f"[id{list_in[0]}|{list_in[1]}]"
        else:
            message = None
        if count == len(list_in[2]):
            num_keyboard = 1
        else:
            num_keyboard = 2
        attachment = f'photo{list_in[0]}_{photo_id[1]}'
        write_result_msg(vk, owner_id, message, content_source, attachment=attachment, num_keyboard=num_keyboard, save_flag=save_flag)
    return list_short_link


def black_white_list(connection, owner_id, id_user, var):
    if var:
        color = 'white'
    else:
        color = 'black'
    db.set_black_white_lists(connection, owner_id, id_user, color)

def get_short_link(token_user, list_in):
    url = "https://api.vk.com/method/utils.getShortLink"
    list_short_link = []
    for item in list_in[2]:
        link = f'https://vk.com/id{list_in[0]}?z=photo{list_in[0]}_{item[1]}'
        values = {
            'url': link,
            'private': 1,
            'access_token': token_user,
            'v': '5.131'
        }
        answer = requests.get(url, params=values)
        data = answer.json()
        short_url = data["response"]["short_url"]
        list_short_link.append(short_url)
        time.sleep(1)
    return list_short_link
