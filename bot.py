import json
from tempfile import TemporaryDirectory
from pathlib import Path
import streamlit as st
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from settings import TOKEN, SPREADSHEET_ID, WORKSHEET_NAME, user_column_map, SCOPE
from datetime import datetime

# CREDS_FILE = './creds/so.json'  # Путь к файлу credential.json

# Инициализация бота
bot = telebot.TeleBot(TOKEN)


# /todo захостить бота и сделать его автономным

# /todo добавить логгирование бота
# Функция для подключения к Google Sheets
def get_gsheet_client():
    cred_str = st.secrets['CREDS']
    creds_obj = json.loads(cred_str)
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)
    json_path = tmp_dir_path / 'creds.json'
    with open(json_path, 'w') as f:
        f.write(json.dumps(creds_obj, indent=2))
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, SCOPE)
    client = gspread.authorize(creds)
    return client


# Функция для записи данных в Google Sheets
def write_to_sheet(value, usr_id, date):
    """Берем текущую дату"""
    if date == "":
        date = datetime.now().strftime("%d.%m.%Y")  # -> "13.04.2025"

    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        """Ищем строку с указанной датой"""
        dates = sheet.col_values(1)  # Получаем все даты из столбца A (он с датами)
        if user_column_map[usr_id]:
            print(user_column_map[usr_id])
            usr_name = user_column_map[usr_id]  # вытаскиваем из словаря столбец пользователя по его tg-id
            col_names = sheet.row_values(1) # список всех имен пользователей
            col_index = col_names.index(usr_name) + 2
            row_num = dates.index(date) + 1  # +1 т.к. нумерация с 1
            print(type(row_num))
            sheet.update_cell(row_num, col_index, value)  # добавляем в последнюю ячейку определенного столбца данные
            print(f'Value "{value}" appended to sheet')

    except Exception as e:
        print(f'An error occurred: {e}')


def plus_message_handlig(message):
    return message.text.startswith('/+') and message.text[2:].isdigit()


#@bot.message_handler(func=lambda message: True)  # временно для отладки
#def debug_all_messages(message):
#    print(f"Сообщение: {message.text}")
#    print(f"Тип чата: {message.chat.type}")
#    print(f"ID чата: {message.chat.id}")


# Обработчик сообщений, начинающихся с "+" и числа
@bot.message_handler(func=plus_message_handlig,
                     chat_types=['group', 'supergroup', 'private'])
def handle_number_message(message):
    number = message.text[1:]
    user_id = str(message.from_user.id)
    date = ""
    print(f'ID пользователя, который ввел данные: {user_id}')
    write_to_sheet(number, user_id, date)  # записываем число в таблицу
    # list_of_data.append(number)  # добавляем число в список
    # count_of_dist += int(number)  # увеличиваем общий счетчик
    # bot.reply_to(message, f'Number {number} has been recorded.')
    bot.set_message_reaction(chat_id=message.chat.id,
                             message_id=message.id,
                             reaction=[telebot.types.ReactionTypeEmoji("✍")]
                             )


# Обработчик сообщений вида: +метры дата_куда_нужно_записать_метры
@bot.message_handler(
    func=lambda message: message.text.startswith('/+') and message.text.split()[0][2:].isdigit() and len(
        message.text.split()) == 2)
def handle_number_with_data_message(message):
    number = message.text.split()[0][1:]
    date = str(message.text.split()[1])
    user_id = str(message.from_user.id)
    print(f'ID пользователя, который ввел данные: {user_id}')
    write_to_sheet(number, user_id, date)  # записываем число в таблицу
    # list_of_data.append(number)  # добавляем число в список
    # count_of_dist += int(number)  # увеличиваем общий счетчик
    bot.reply_to(message, f'Number {number} has been recorded on the date {date}')
    bot.set_message_reaction(chat_id=message.chat.id,
                             message_id=message.id,
                             reaction=[telebot.types.ReactionTypeEmoji("✍")]
                             )

# @bot.message_handler(commands=['list'])
# def print_list_of_data(message):
#     bot.reply_to(message, f'Текущий список: {list_of_data}')


# @bot.message_handler(commands=['count'])
# def count_of_data(message):
#     bot.reply_to(message, f'Общее количество метров: {count_of_dist}')


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Hello! I'm a bot that records numbers from messages starting with '+' into a Google Sheet.")


st.write('Bot is running...')
bot.polling(none_stop=True, interval=0)
