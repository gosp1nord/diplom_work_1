import sqlalchemy
import json
from custom_logs import write_log

def get_info_connect_db():
    list_info = []
    with open("custom_data/db_connect.txt", 'r', encoding='utf-8') as f:
        for line in f:
            list_info.append(line.strip())
    return list_info

def create_tables(connection):
    connection.execute("""
    CREATE table if not exists users(
            owner_id integer primary key,
            step varchar(10),
            white_list_ids integer[],
            black_list_ids integer[],
            temp_saved_list_ids integer[],
            user_current_id integer,
            city_number integer,
            city_name text,
            age integer,
            sex integer,
            status integer
            );
    """)

def create_table_for_out(connection, owner_id):
    connection.execute(f"""
    CREATE table if not exists t_{owner_id}(
            dict_key numeric(6,3) primary key,
            dict_value integer[]
            );
    """)



def set_line_for_user(connection, owner_id):
    try:
        connection.execute(f"INSERT INTO users(owner_id) VALUES ('{owner_id}');")
        connection.execute(f"UPDATE users SET step = '1' WHERE owner_id = '{owner_id}';")
    except Exception as e:
        print("Запись с таким id уже есть")
        # print(e)

def set_step(connection, owner_id, step):
    connection.execute(f"UPDATE users SET step = '{step}' WHERE owner_id = '{owner_id}';")

def set_black_white_lists(connection, owner_id, list_ids, color):
    connection.execute(f"UPDATE users SET {color}_list_ids = array_append({color}_list_ids, '{list_ids}') WHERE owner_id = '{owner_id}';")

def set_dict_weight(connection, owner_id, dict_weight):
    res = json.dumps(dict_weight)
    connection.execute(f"UPDATE users SET dict_user_ids = '{res}' WHERE owner_id = '{owner_id}';")

def set_temp_saved_list(connection, owner_id, list_ids):
    for item in list_ids:
        connection.execute(f"UPDATE users SET temp_saved_list_ids = array_append(temp_saved_list_ids, '{item}') WHERE owner_id = '{owner_id}';")

def set_table_for_out(connection, owner_id, dict_user_ids):
    for key in dict_user_ids:
        connection.execute(f"INSERT INTO t_{owner_id}(dict_key) VALUES ('{key}');")
        for item in dict_user_ids[key]:
            connection.execute(f"UPDATE t_{owner_id} SET dict_value = array_append(dict_value, '{item}') WHERE dict_key = '{key}';")

def set_settings(connection, owner_id, atr_name='clear', atr_value=0):
    list_atr = ['city_number', 'city_name', 'age', 'sex', 'status']
    if atr_name == 'clear':
        for item in list_atr:
            connection.execute(f"UPDATE users SET {item} = NULL WHERE owner_id = '{owner_id}';")
    else:
        connection.execute(f"UPDATE users SET {atr_name} = '{atr_value}' WHERE owner_id = '{owner_id}';")

def set_user_current_id(connection, owner_id, user_current_id):
    if user_current_id:
        connection.execute(f"UPDATE users SET user_current_id = '{user_current_id}' WHERE owner_id = '{owner_id}';")
    else:
        connection.execute(f"UPDATE users SET user_current_id = NULL WHERE owner_id = '{owner_id}';")



def get_step(connection, owner_id):
    res = connection.execute(f"SELECT step FROM users WHERE owner_id = '{owner_id}';").fetchone()
    return res[0]

def get_black_white_lists(connection, owner_id, color):
    res = connection.execute(f"SELECT {color}_list_ids FROM users WHERE owner_id = '{owner_id}';").fetchone()
    return res[0]

def get_dict_weight(connection, owner_id):
    res = connection.execute(f"SELECT dict_user_ids FROM users WHERE owner_id = '{owner_id}';").fetchone()
    return res[0]

def get_id_from_temp_saved_list(connection, owner_id):
    res = connection.execute(f"SELECT temp_saved_list_ids FROM users WHERE owner_id = '{owner_id}';").fetchone()
    if res[0]:
        out_id = res[0].pop()
        connection.execute(f"UPDATE users SET temp_saved_list_ids = NULL WHERE owner_id = '{owner_id}';")
        for item in res[0]:
            connection.execute(f"UPDATE users SET temp_saved_list_ids = array_append(temp_saved_list_ids, '{item}') WHERE owner_id = '{owner_id}';")
    else:
        out_id = False
    return out_id

def get_id_from_table_for_out(connection, owner_id):
    count_res = connection.execute(f"SELECT count(*) FROM t_{owner_id};").fetchone()
    if count_res[0]:
        list_dict_value = connection.execute(f"SELECT dict_value, dict_key FROM t_{owner_id} WHERE dict_key = (SELECT MAX(dict_key) FROM t_{owner_id});").fetchone()
        out_id = list_dict_value[0].pop()
        if len(list_dict_value[0]):
            connection.execute(f"UPDATE t_{owner_id} SET dict_value = NULL WHERE dict_key = '{list_dict_value[1]}';")
            for item in list_dict_value[0]:
                connection.execute(f"UPDATE t_{owner_id} SET dict_value = array_append(dict_value, '{item}') WHERE dict_key = '{list_dict_value[1]}';")
        else:
            connection.execute(f"DELETE FROM t_{owner_id} WHERE dict_key = '{list_dict_value[1]}';")
        return out_id
    else:
        del_table(connection, f't_{owner_id}')

def get_settings(connection, owner_id):
    answer_settings = []
    list_city = []
    list_city.append(connection.execute(f"SELECT city_number FROM users WHERE owner_id = '{owner_id}';").fetchone()[0])
    list_city.append(connection.execute(f"SELECT city_name FROM users WHERE owner_id = '{owner_id}';").fetchone()[0])
    answer_settings.append(list_city)
    answer_settings.append(connection.execute(f"SELECT age FROM users WHERE owner_id = '{owner_id}';").fetchone()[0])
    answer_settings.append(connection.execute(f"SELECT sex FROM users WHERE owner_id = '{owner_id}';").fetchone()[0])
    answer_settings.append(connection.execute(f"SELECT status FROM users WHERE owner_id = '{owner_id}';").fetchone()[0])
    return answer_settings

def get_user_current_id(connection, owner_id):
    user_current_id = connection.execute(f"SELECT user_current_id FROM users WHERE owner_id = '{owner_id}';").fetchone()[0]
    return user_current_id




def del_record(connection, owner_id, column):
    connection.execute(f"UPDATE users SET {column} = NULL WHERE owner_id = '{owner_id}';")

def del_table(connection, name_table):
    connection.execute(f"DROP TABLE {name_table};")

def check_table(connection, owner_id):
    res = connection.execute(f"SELECT exists (SELECT * FROM information_schema.tables WHERE table_name = 't_{owner_id}' and table_schema = 'public');").fetchone()
    return res[0]



def get_connect():
    list_info = get_info_connect_db()
    db = f'postgresql://{list_info[0]}:{list_info[1]}@{list_info[2]}:{list_info[3]}/{list_info[4]}'
    try:
        engine = sqlalchemy.create_engine(db)
        connection = engine.connect()
        return connection
    except Exception as e:
        print("Ошибка подключения к БД PostgreSQL. Убедитесь, что установлен необходимый для работы драйвер БД, проверьте правильность данных для подключения в файле db_connect.txt")
        print(e)
        write_log("Ошибка подключения к БД PostgreSQL. Убедитесь, что установлен необходимый для работы драйвер БД, проверьте правильность данных для подключения в файле db_connect.txt")
        exit()

