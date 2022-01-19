import os.path
from datetime import datetime


if os.path.isfile('custom_data/logs.txt'):
    pass
else:
    with open('custom_data/logs.txt', 'w', encoding="utf-8") as file_0:
        pass


def write_log(text):
    tt = datetime.now().timetuple()
    res = f"{tt[2]}-{tt[1]}-{tt[0]} {tt[3]}:{tt[4]}:{tt[5]}"
    with open("custom_data/logs.txt", "a", encoding="utf-8") as f:
        f.write(f'[{res}] {text}\n')
