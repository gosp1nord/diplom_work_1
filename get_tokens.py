import requests


def get_tokens():
    with open("custom_data/token_group.txt", 'r', encoding='utf-8') as f:
        token_group = f.read().strip()
    with open("custom_data/token_user.txt", 'r', encoding='utf-8') as f:
        token_user = f.read().strip()
    with open("custom_data/group_id.txt", 'r', encoding='utf-8') as f:
        group_id = f.read().strip()
    return token_group, token_user, group_id

def chek_tokens(token_group, token_user, group_id):
    params_user = {
        'access_token': token_user,
        'v': '5.131'
    }
    params_group = {
        'access_token': token_group,
        'group_id': group_id,
        'v': '5.131'
    }
    url = f"https://api.vk.com/method/account.getInfo"
    link = f"https://api.vk.com/method/groups.getById"
    try:
        response = requests.get(url, params=params_user)
        if "error" in response.json():
            return f'Ошибка проверки ключа пользователя: {response.json()["error"]["error_msg"]}'
        response = requests.get(link, params=params_group)
        if "error" in response.json():
            return f'Ошибка проверки ключа группы: {response.json()["error"]["error_msg"]}'
    except Exception as e:
        return f"Ошибка запроса проверки ключей: {e}"
    return False