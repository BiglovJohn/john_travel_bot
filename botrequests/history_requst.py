import sqlite3

from telebot.types import Message

from config import bot


def process_history_request(message: Message) -> None:

    """
    Функция для получения и отправки пользователю истории запросов по команде 'history'

    :return: None

    USER_ID (int): id пользователя
    """

    USER_ID = int(message.from_user.id)
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    sqlite_select_query = f"""SELECT * FROM hotels_result_db WHERE user_id = {USER_ID}"""
    cursor.execute(sqlite_select_query)
    records = cursor.fetchall()

    if len(records) <= 5:
        for i in range(len(records)):
            history_result = ('Команда: {command}\nДата и время запроса: {req}\nБыл найден отель: {hotel_history}'.format(
                command=records[-i][7],
                req=records[-i][1],
                hotel_history=records[-i][2])
            )
            bot.send_message(message.chat.id, history_result)
    else:
        for i in range(5):
            history_result = ('Команда: {command}\nДата и время запроса: {req}\nБыл найден отель: {hotel_history}'.format(
                command=records[-i][7],
                req=records[-i][1],
                hotel_history=records[-i][2])
            )
            bot.send_message(message.chat.id, history_result)
