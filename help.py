from random import randrange


def write_help(vk, user_id):
    message = """
    Сервис поиска аккаунтов пользователей. Для начала работы - отправьте сообщение со словом "старт"\n
    Во время подготовки к поиску Вам будет предложено ответить на несколько вопросов для уточнения параметров поиска.\n
    В процессе просмотра результатов Вы можете сохранить понравившиеся профили, либо наоборот, отправить их в стоп-лист.
    А также поставить лайк на понравившиеся фото профиля. Для этих действий будут доступны кнопки виртуальной клавиатуры.
    В момент, когда робот ждет от Вас сообщение, Вы можете остановить работу робота, отправив сообщение со словом "стоп".\n
    Чтобы просмотреть сохраненные профили - отправьте в сообщении слово "/сохранено". А очистить стоп-лист можно командой "/очистить".
    """
    values = {
        'message': message,
        'user_id': user_id,
        'random_id': randrange(10 ** 7),
    }
    vk.method('messages.send', values=values)