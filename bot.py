import telebot
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from settings import TOKEN, SPREADSHEET_ID, WORKSHEET_NAME, user_column_map, SCOPE

CREDS_FILE = './creds/so_test.json'  # Путь к файлу credential.json

# Инициализация бота
bot = telebot.TeleBot(TOKEN)


# /todo Сделать привязку текущей даты к строке таблицы, чтобы метры записывались в нужную дату.
#  Либо костыльно, либо считывать таблицу


# Функция для подключения к Google Sheets
def get_gsheet_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client


# Функция для записи данных в Google Sheets
def write_to_sheet(value, usr_id):
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

        if user_column_map[usr_id]:
            column = user_column_map[usr_id]  # вытаскиваем из словаря столбец пользователя по его tg-id
            last_row = len(sheet.col_values(column))  # считаем, сколько в этом столбце уже есть записей
            sheet.update_cell(last_row + 1, column, value)  # добавляем в последнюю ячейку определенного столбца данные
            print(f'Value "{value}" appended to sheet')

    except Exception as e:
        print(f'An error occurred: {e}')


# Обработчик сообщений, начинающихся с "+" и числа
@bot.message_handler(func=lambda message: message.text.startswith('+') and message.text[1:].isdigit())
def handle_number_message(message):
    number = message.text[1:]
    user_id = str(message.from_user.id)
    print(f'ID пользователя, который ввел данные: {user_id}')
    write_to_sheet(number, user_id)  # записываем число в таблицу
    # list_of_data.append(number)  # добавляем число в список
    # count_of_dist += int(number)  # увеличиваем общий счетчик
    bot.reply_to(message, f'Number {number} has been recorded.')


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


# Запуск бота
if __name__ == '__main__':
    print('Bot is running...')
    bot.polling(none_stop=True)
