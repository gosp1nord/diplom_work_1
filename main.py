import db_connect as db
import get_tokens as gtk
import json
import requests
import vk_api
from custom_logs import write_log
from datetime import datetime
from help import write_help
from posting_results import set_result_in_chat, write_result_msg, black_white_list
from random import randrange
from setting_search import get_cities
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


def write_msg(vk, user_id, message, list_city=None, num_keyboard=0):
    keyboard_in = VkKeyboard(one_time=False, inline=True)
    values = {
        'user_id': user_id,
        'message': message,
        'random_id': randrange(10 ** 7)
    }
    if num_keyboard == 1:
        for i, item in enumerate(list_city):
            info = f"{item[1][0]}{item[1][len(item[1]) - 1]}"
            text_button = (info[:37] + '...') if len(info) > 40 else info
            if i < (len(list_city)-1):
                keyboard_in.add_callback_button(text_button, VkKeyboardColor.POSITIVE, payload=f'{item[0]}')
                keyboard_in.add_line()
            else:
                keyboard_in.add_callback_button(text_button, VkKeyboardColor.POSITIVE, payload=f'{item[0]}')
        values['keyboard'] = keyboard_in.get_keyboard()
    elif num_keyboard == 2:
        payload_data = ['100001', '100002']
        for i, item in enumerate(list_city):
            keyboard_in.add_callback_button(item, VkKeyboardColor.POSITIVE, payload=payload_data[i])
        values['keyboard'] = keyboard_in.get_keyboard()

    res = vk.method('messages.send', values=values)
    return res


def mssgs(connection, token_group, token_user, group_id, owner_id=''):
    vk = vk_api.VkApi(token=token_group)
    longpoll = VkBotLongPoll(vk, group_id)
    if owner_id:
        message = 'Для начала взаимодействия - отправьте сообщение со словом "старт"\nДля получения справки по функционалу - "помощь"'
        write_msg(vk, owner_id, message)
    step = '1'
    list_city = []
    first_city_flag = False
    dict_for_delete_msg = dict()
    current_city = []
    message_final = ''
    list_yes_no = ["Да", "Нет"]
    res_set_one_user = []
    # user_current_id = ''
    save_flag = False
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            request = event.message['text']
            owner_id = event.object['message']['from_id']
            db.set_line_for_user(connection, owner_id)
            step = db.get_step(connection, owner_id)

            if request.lower() == "привет" and step == '1':
                message = 'Привет!\nЯ смогу помочь в поиске отношений. Для начала поиска напиши "старт".'
                write_msg(vk, owner_id, message)
            elif request.lower() == "помощь":
                write_help(vk, owner_id)
                if step == '6':
                    message = '--------------------------------'
                    content_source = f'{{"type": "url", "url": "https://vk.com/id{owner_id}"}}'
                    write_result_msg(vk, owner_id, message, content_source)

            elif request.lower() == "/сохранено":
                save_list_ids = db.get_black_white_lists(connection, owner_id, "white")
                if save_list_ids:
                    db.set_temp_saved_list(connection, owner_id, save_list_ids)
                    db.set_step(connection, owner_id, '6')
                    save_flag = True
                    message = 'Сохраненные пользователи:'
                    write_msg(vk, owner_id, message)
                    user_current_id = get_id_from_base(connection, owner_id, save_flag)
                    db.set_user_current_id(connection, owner_id, user_current_id)
                    res_set_one_user = get_pars_photos(token_user, user_current_id, vk, owner_id, save_flag=True)
                else:
                    message = 'Сохраненных пользователей не найдено.'
                    write_msg(vk, owner_id, message)

            elif request.lower() == "/очистить":
                db.del_record(connection, owner_id, 'black_list_ids')
                message = 'Стоп-лист пустой.'
                write_msg(vk, owner_id, message)

            elif request.lower() == 'стоп':
                if step == '2':
                    try:
                        dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                        vk.method('messages.delete', values=dict_for_delete_msg)
                    except Exception as e:
                        print(f"не удалось удалить сообщение на шаге {step}")
                        print(e)
                db.set_step(connection, owner_id, '1')
                db.del_record(connection, owner_id, 'temp_saved_list_ids')
                db.set_settings(connection, owner_id, atr_name='clear', atr_value=0)
                message = 'Работа остановлена.\nДля возобновления работы отправьте слово "старт"'
                write_msg(vk, owner_id, message)
                write_log(f'Остановка поиска для id{owner_id}')
                save_flag = False

            elif step == '1':
                if request.lower() == "начать" or request.lower() == "старт" or request.lower() == "start" or request.lower() == "/start" or request.lower() == "/старт":
                    result_check_dir = check_last_finding(connection, owner_id)
                    if result_check_dir:
                        message = 'Остались непросмотренные результаты с прошлого поиска. Продолжить их?\n"Да" - продолжить\n"Нет" - начнем заново.'
                        write_msg(vk, owner_id, message, list_city=list_yes_no, num_keyboard=2)
                    else:
                        text = f'Для начала работы нужно настроить параметры поиска:\n- город,\n- возраст,\n- пол,\n- отношения.\nПоиск будет производиться только открытых аккаунтов. Начнем с названия города - впишите его в ответном сообщении...'
                        write_msg(vk, owner_id, text)
                        write_log(f'Старт настроек поиска для id{owner_id}')
                        db.set_step(connection, owner_id, '2')
                else:
                    write_msg(vk, owner_id, 'Не понял вашего ответа...\nДля начала взаимодействия - отправьте сообщение со словом "старт"\nДля получения справки по функционалу - "помощь"')
            elif step == '2':
                if first_city_flag:
                    try:
                        dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                        vk.method('messages.delete', values=dict_for_delete_msg)
                    except Exception as ex:
                        print("Не удалось удалить сообщение на шаге 2")
                        print(ex)
                list_city = get_cities(token_user, request)
                if len(list_city) != 0:
                    message = 'Выберите город из предложенных вариантов или впишите снова свой вариант:'
                    write_msg(vk, owner_id, message, list_city=list_city, num_keyboard=1)
                    first_city_flag = True
                else:
                    message = 'Ничего не смог найти. Попробуйте снова...'
                    write_msg(vk, owner_id, message, num_keyboard=0)
            elif step == '3':
                message = 'Возраст для поиска? (только цифры, от 18 до 100)...'
                try:
                    age = int(event.message['text'])
                    if age < 18 or age > 100:
                        message_ex = 'Пожалуйста, пишите корректные цифры возраста. Допустимо писать цифры от 18 до 100.'
                        write_msg(vk, owner_id, message_ex, num_keyboard=0)
                    else:
                        db.set_settings(connection, owner_id, atr_name='age', atr_value=age)
                        db.set_step(connection, owner_id, '4')
                        message = 'Выбрать пол для поиска...'
                        list_temp = ["М", "Ж"]
                        write_msg(vk, owner_id, message, list_city=list_temp, num_keyboard=2)
                except Exception as e:
                    print(e)
                    message_ex = 'Нужно писать только цифры! Или "стоп", если хотите остановить поиск и начать сначала.\n'
                    write_msg(vk, owner_id, message_ex, num_keyboard=0)
                    write_msg(vk, owner_id, message, num_keyboard=0)
            elif step == '4':
                list_temp = ["М", "Ж"]
                dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                vk.method('messages.delete', values=dict_for_delete_msg)
                message = f'Сообщение не распознано!\nВыбрать пол для поиска, нажав одну из кнопок (или напишите "стоп", чтобы остановить поиск и начать сначала)...'
                write_msg(vk, owner_id, message, list_city=list_temp, num_keyboard=2)
            elif step == '5':
                message = f'Сообщение не распознано!\nВыбрать, состоит ли в отношениях тот, кого ищем?\nНужно нажать одну из кнопок (или напишите "стоп", чтобы остановить поиск и начать сначала)...'
                write_msg(vk, owner_id, message, list_city=list_yes_no, num_keyboard=2)
            elif step == '6':
                message = f'Сообщение не распознано!\nДля выбора действия - нажмите кнопку\n(или напишите "стоп", чтобы остановить поиск и начать сначала)...'
                user_current_id = db.get_user_current_id(connection, owner_id)
                content_source = f'{{"type": "url", "url": "https://vk.com/id{user_current_id}"}}'
                write_result_msg(vk, owner_id, message, content_source)

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            owner_id = event.object['user_id']
            step = db.get_step(connection, owner_id)
            if step == '1':
                dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                vk.method('messages.delete', values=dict_for_delete_msg)
                if event.object['payload'] == 100001:
                    write_log(f'Продолжение просмотра предыдущего поиска для id{owner_id}')
                    user_current_id = get_id_from_base(connection, owner_id, save_flag)
                    db.set_user_current_id(connection, owner_id, user_current_id)
                    res_set_one_user = get_pars_photos(token_user, user_current_id, vk, owner_id, save_flag)
                    db.set_step(connection, owner_id, '6')
                elif event.object['payload'] == 100002:
                    db.del_table(connection, f't_{owner_id}')
                    text = f'Для начала работы нужно настроить параметры поиска:\n- город,\n- возраст,\n- пол,\n- отношения.\nПоиск будет производиться только открытых аккаунтов. Начнем с названия города - впишите его в ответном сообщении...'
                    write_msg(vk, owner_id, text)
                    write_log(f'Старт настроек поиска для id{owner_id}')
                    db.set_settings(connection, owner_id, atr_name='clear', atr_value=0)
                    db.set_step(connection, owner_id, '2')
            elif step == '2':
                if event.object['payload'] == 100001 and len(current_city) != 0:
                    dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                    vk.method('messages.delete', values=dict_for_delete_msg)
                    write_msg(vk, owner_id, message_final, num_keyboard=0)
                    db.set_settings(connection, owner_id, atr_name='city_number', atr_value=current_city[0])
                    db.set_settings(connection, owner_id, atr_name='city_name', atr_value=current_city[1][0])
                    db.set_step(connection, owner_id, '3')
                    message = 'Возраст для поиска? (только цифры, от 18 до 100)...'
                    write_msg(vk, owner_id, message, num_keyboard=0)
                elif event.object['payload'] == 100002 and len(current_city) != 0:
                    dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                    vk.method('messages.delete', values=dict_for_delete_msg)
                    message = 'Попробуйте снова...'
                    write_msg(vk, event.object['user_id'], message, num_keyboard=0)
                else:
                    for item in list_city:
                        if item[0] == event.object['payload']:
                            dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                            vk.method('messages.delete', values=dict_for_delete_msg)
                            current_city = item
                            message_final = 'Выбран город:\n'
                            for i in item[1]:
                                message_final = message_final + i
                            message = message_final + "\nПравильно?"
                            write_msg(vk, owner_id, message, list_city=list_yes_no, num_keyboard=2)
                            break
            elif step == '4':
                sex = 1
                if event.object['payload'] == 100001:
                    message_final = 'Выбран пол - мужской'
                    sex = 2
                elif event.object['payload'] == 100002:
                    message_final = 'Выбран пол - женский'
                    sex = 1
                dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                vk.method('messages.delete', values=dict_for_delete_msg)
                write_msg(vk, owner_id, message_final, num_keyboard=0)
                db.set_settings(connection, owner_id, atr_name='sex', atr_value=sex)
                db.set_step(connection, owner_id, '5')
                message = 'Состоит ли в отношениях с кем-то? В ответ прислать цифру:\n"Да" - есть отношения (в браке, в гражданском браке, в отношениях и т.д.)\n"Нет" - не в отношениях'
                write_msg(vk, owner_id, message, list_city=list_yes_no, num_keyboard=2)
            elif step == '5':
                status = 2
                if event.object['payload'] == 100001:
                    message_final = 'Выбрано - есть отношения'
                    status = 1
                elif event.object['payload'] == 100002:
                    message_final = 'Выбрано - нет отношений'
                    status = 2
                dict_for_delete_msg = get_dict_for_delete(vk, owner_id, group_id, token_user)
                vk.method('messages.delete', values=dict_for_delete_msg)
                write_msg(vk, owner_id, message_final, num_keyboard=0)
                db.set_settings(connection, owner_id, atr_name='status', atr_value=status)
                message = "\nПоиск..."
                write_msg(vk, owner_id, message, num_keyboard=0)
                ###################################################################################
                answer_settings = db.get_settings(connection, owner_id)
                len_ids = main_search(connection, answer_settings, owner_id, token_user)
                if len_ids == 0:
                    message = f'По этим настройкам никого не найдено. Попробуйте снова...'
                    write_log(f'Для id{owner_id} найдено {len_ids} аккаунтов.')
                    write_msg(vk, owner_id, message, num_keyboard=0)
                    db.set_step(connection, owner_id, '1')
                    db.set_settings(connection, owner_id, atr_name='clear', atr_value=0)
                else:
                    message = f'Найдено {len_ids} аккаунтов. Идет обработка...'
                    write_log(f'Для id{owner_id} найдено {len_ids} аккаунтов.')
                    write_msg(vk, owner_id, message, num_keyboard=0)
                    second_phase(token_user, owner_id, connection)
                    user_current_id = get_id_from_base(connection, owner_id, save_flag)
                    db.set_user_current_id(connection, owner_id, user_current_id)
                    res_set_one_user = get_pars_photos(token_user, user_current_id, vk, owner_id, save_flag)
                    db.set_step(connection, owner_id, '6')

            elif step == '6':
                user_current_id = db.get_user_current_id(connection, owner_id)
                content_source = f'{{"type": "url", "url": "https://vk.com/id{user_current_id}"}}'
                if event.object['payload'] == 303:
                    message = f"{res_set_one_user[1]}"
                    write_result_msg(vk, owner_id, message, content_source, num_keyboard=0)
                    message = f"Можно перейти по любой ссылке и поставить лайк фотке\n"
                    for link in res_set_one_user[0]:
                        message = message + f'{link}\n'
                    write_result_msg(vk, owner_id, message, content_source, num_keyboard=3)

                elif event.object['payload'] == 301:
                    user_current_id = db.get_user_current_id(connection, owner_id)
                    black_white_list(connection, owner_id, user_current_id, 0)
                    message = f'--------------------------\n\nПользователь "{res_set_one_user[1]}" добавлен в стоп-лист и исключен из поиска.'
                    write_result_msg(vk, owner_id, message, content_source, num_keyboard=3)

                elif event.object['payload'] == 302:
                    user_current_id = db.get_user_current_id(connection, owner_id)
                    black_white_list(connection, owner_id, user_current_id, 1)
                    message = f'--------------------------\n\nПользователь "{res_set_one_user[1]}" сохранен.'
                    write_result_msg(vk, owner_id, message, content_source, num_keyboard=3)

                elif event.object['payload'] == 304:
                    message = '--------------------------'
                    write_result_msg(vk, owner_id, message, content_source, num_keyboard=0)
                    user_current_id = get_id_from_base(connection, owner_id, save_flag)
                    db.set_user_current_id(connection, owner_id, user_current_id)
                    if user_current_id:
                        res_set_one_user = get_pars_photos(token_user, user_current_id, vk, owner_id, save_flag)
                    else:
                        db.set_step(connection, owner_id, '1')
                        db.set_settings(connection, owner_id, atr_name='clear', atr_value=0)
                        message = 'Пользователей больше нет.\nДля возобновления поиска отправьте слово "старт"'
                        write_msg(vk, owner_id, message)
                        save_flag = False

        if event.type == VkBotEventType.MESSAGE_REPLY:
            if step == '4' or step == '5':
                dict_for_delete_msg['conversation_message_id'] = event.object['conversation_message_id']


def get_dict_for_delete(vk, owner_id, group_id, token_user):
    values = {
        'user_id': owner_id,
        'access_token': token_user,
        'v': '5.131'
    }
    res_messages = vk.method('messages.getHistory', values=values)
    with open(f'temp/temp_history.json', 'w', encoding='utf-8') as file12:
        json.dump(res_messages, file12)
    for item in res_messages['items']:
        if item['from_id'] == int(f'-{group_id}'):
            dict_for_delete_msg = {
                'peer_id': owner_id,
                'message_ids': item['id'],
                'conversation_message_id': item['conversation_message_id'],
                'delete_for_all': 1
            }
            return dict_for_delete_msg


def check_last_finding(connection, owner_id):
    res = db.check_table(connection, owner_id)
    return res

def main_search(connection, answer_settings, owner_id, token_user):
    city = answer_settings[0][0]
    age = answer_settings[1]
    start_year = datetime.now().year - age
    sex = answer_settings[2]
    marital_status = answer_settings[3]
    if marital_status == 1:
        list_marital_status = [3, 4, 7, 8]
    else:
        list_marital_status = [1, 2, 5, 6]
    temp_list_result = []
    while True:
        for j in range(1, 3):
            get_info_about_users(token_user, sex, city, start_year, j)
            if j == 1:
                a, b = 1, 7
            else:
                a, b = 7, 13
            for k in range(a, b):
                res = parsing_result(k, city, list_marital_status)
                for i in res:
                    if i not in temp_list_result:
                        temp_list_result.append(i)
        break
    list_result = check_black_white_list(connection, owner_id, temp_list_result)
    with open('temp/temp_result_ids.txt', 'w', encoding='utf-8') as file:
        for item in list_result:
            file.write(str(item) + '\n')
    return len(list_result)


def second_phase(token_user, owner_id, connection):
    list_user_id = [owner_id]
    data_user_groups = get_info_about_user_group(token_user, list_user_id)
    if data_user_groups['response'][0]['groups'] == False:
        user_owner_groups = [0]
    else:
        user_owner_groups = pars_data_groups(data_user_groups)

    full_list_ids_user = []
    with open('temp/temp_result_ids.txt', 'r', encoding='utf-8') as file:
        for item in file:
            full_list_ids_user.append(item.strip())

    list_users_groups = []
    while True:
        work_list = [full_list_ids_user.pop() for i in range(25) if len(full_list_ids_user) != 0]
        if len(work_list):
            data_users_groups = get_info_about_user_group(token_user, work_list)
            for i in pars_data_groups(data_users_groups, 0):
                list_users_groups.append(i)
        else:
            break

    dict_weight_users = dict()
    for ittrz in list_users_groups:
        count = 0
        for i in user_owner_groups:
            if i in ittrz[1]:
                count += 1
        weight = round((count * 100) / len(user_owner_groups), 3)
        if f"{weight}" in dict_weight_users:
            temp = dict_weight_users[f"{weight}"]
            temp.append(ittrz[0])
            dict_weight_users[f"{weight}"] = temp
        else:
            dict_weight_users[f"{weight}"] = [ittrz[0]]
    db.create_table_for_out(connection, owner_id)
    db.set_table_for_out(connection, owner_id, dict_weight_users)
    return dict_weight_users


def get_id_from_base(connection, owner_id, save_flag):
    if save_flag:
        current_id = db.get_id_from_temp_saved_list(connection, owner_id)
    else:
        current_id = db.get_id_from_table_for_out(connection, owner_id)
    return current_id

def get_pars_photos(token_user, current_id, vk, owner_id, save_flag):
    answer_for_photos = get_foto_user(token_user, current_id)
    list_id_photos = pars_data_with_photos(answer_for_photos)
    if list_id_photos:
        list_name_and_photos_user = [current_id, get_name_one_user(token_user, current_id), list_id_photos]
        # #######################################
        res_set_one_user = set_result_in_chat(vk=vk, owner_id=owner_id, token_user=token_user, list_in=list_name_and_photos_user, save_flag=save_flag)
        return [res_set_one_user, list_name_and_photos_user[1]]
        # ######################################
    else:
        return False


def check_black_white_list(connection, owner_id, temp_list_result):
    res_list = temp_list_result
    temp_list_color = ['white', 'black']
    for i in range(2):
        temp_list = db.get_black_white_lists(connection, owner_id, temp_list_color[i])
        if temp_list:
            res_list = list(set(res_list) - set(temp_list))
    return res_list

def get_info_about_user_group(token_user, work_list):
    url = f"https://api.vk.com/method/execute"

    test_str = f"""
        var array1 = {{}};
        var array2 = {work_list};
        var b = {len(work_list)};
        while (b != 0) {{
        var user_id = array2.pop();
        var mon1 = API.groups.get({{"user_id": user_id, "count": 1000}});
        b = b - 1;
        array1.push({{"user_id": user_id, "groups": mon1}});
        }};
        return array1;
        """
    values = {
        'access_token': token_user,
        'code': test_str,
        'v': '5.131'
    }

    wall = requests.get(url, params=values)
    data = wall.json()
    with open('temp/temp_group.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    return data


def pars_data_groups(data_groups, num_var=1):
    list_groups = []
    if num_var:
        for item in data_groups['response'][0]['groups']['items']:
            list_groups.append(item)
    else:
        for item in data_groups['response']:
            if item['groups']:
                list_groups.append([item['user_id'], item['groups']['items']])
    return list_groups


def get_foto_user(token_user, id_user):
    url = f"https://api.vk.com/method/photos.get"
    values = {
        "owner_id": id_user,
        "album_id": "profile",
        "extended": 1,
        "count": 1000,
        'access_token': token_user,
        'v': '5.131'
    }
    wall = requests.get(url, params=values)
    data = wall.json()
    with open('temp/temp_photo_answer.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    return data

def pars_data_with_photos(data_photos):
    if data_photos['response']['items']:
        list_ids_photos = []
        for item in data_photos['response']['items']:
            if len(item) < 4:
                list_ids_photos.append(item['id'])
            else:
                count = int(item['likes']['count']) + int(item['comments']['count'])
                list_ids_photos.append([count, item['id']])
                list_ids_photos.sort(key=lambda x: x[0], reverse=True)
                list_ids_photos = list_ids_photos[:3]
        return list_ids_photos
    else:
        print("Фоток нет")
        return False

def get_name_one_user(token_user, id_user):
    url = f"https://api.vk.com/method/users.get"
    values = {
        "user_ids": id_user,
        "fields": "first_name, last_name",
        'access_token': token_user,
        'v': '5.131'
    }
    wall = requests.get(url, params=values)
    data = wall.json()
    answer = f"{data['response'][0]['first_name']} {data['response'][0]['last_name']}"
    return answer


def parsing_result(k, city, list_marital_status):
    list_id_temp = []
    with open('temp/temp.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    for i in range(len(data[f'{k}']['items'])):
        if 'city' in data[f'{k}']['items'][i]:
            if data[f'{k}']['items'][i]['city']['id'] != city:
                continue
        else:
            continue
        if 'is_closed' in data[f'{k}']['items'][i]:
            if data[f'{k}']['items'][i]['is_closed']:
                continue
        else:
            continue
        if 'relation' in data[f'{k}']['items'][i]:
            if data[f'{k}']['items'][i]['relation'] in list_marital_status:
                continue
        list_id_temp.append(data[f'{k}']['items'][i]['id'])
    return list_id_temp


def get_info_about_users(token_user, sex, city, year, half_year):
    url = f"https://api.vk.com/method/execute"
    if half_year == 1:
        test_str = f"""
            var mon1 = API.users.search({{"sex": {sex},"birth_month":1,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon2 = API.users.search({{"sex": {sex},"birth_month":2,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon3 = API.users.search({{"sex": {sex},"birth_month":3,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon4 = API.users.search({{"sex": {sex},"birth_month":4,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon5 = API.users.search({{"sex": {sex},"birth_month":5,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon6 = API.users.search({{"sex": {sex},"birth_month":6,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var res = {{"1": mon1, "2": mon2, "3": mon3, "4": mon4, "5": mon5, "6": mon6}};
            return res;
            """
    else:
        test_str = f"""
            var mon7 = API.users.search({{"sex": {sex},"birth_month":7,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon8 = API.users.search({{"sex": {sex},"birth_month":8,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon9 = API.users.search({{"sex": {sex},"birth_month":9,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon10 = API.users.search({{"sex": {sex},"birth_month":10,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon11 = API.users.search({{"sex": {sex},"birth_month":11,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var mon12 = API.users.search({{"sex": {sex},"birth_month":12,"birth_year":{year},"fields":"relation, city, personal","city": {city},"has_photo": 1,"count": 1000}});
            var res = {{"7": mon7, "8": mon8, "9": mon9, "10": mon10, "11": mon11, "12": mon12}};
            return res;
            """
    values = {
        'access_token': token_user,
        'code': test_str,
        'v': '5.131'
    }
    wall = requests.get(url, params=values)
    data = wall.json()
    with open('temp/temp.json', 'w', encoding='utf-8') as file:
        json.dump(data['response'], file, indent=4, ensure_ascii=False)


def main_main():
    token_group, token_user, group_id = gtk.get_tokens()
    res_chek = gtk.chek_tokens(token_group, token_user, group_id)
    owner_id = ''
    if res_chek:
        write_log(res_chek)
        exit()
    connection = db.get_connect()
    db.create_tables(connection)
    print("старт")
    while True:
        mssgs(connection, token_group, token_user, group_id, owner_id)
        print("Рестарт")


if __name__ == "__main__":
    main_main()

