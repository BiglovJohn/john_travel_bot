import logging

from config import bot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar
from datetime import date, datetime, timedelta
from botrequests.lowprice_request import get_data_low
from botrequests.highprice_request import get_data_high
from botrequests.bestdeal_request import get_data_best
from db import db_table_val, conn, cursor

"""Последовательно собираем необходимые от пользователя данные для записи в БД и передачи в запрос к API"""

logging.basicConfig(filename='travel_bot_logs.log',
                    format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p',
                    encoding='utf-8',
                    level=logging.INFO
                    )


def restart_function(message):
    bot.send_message(message.from_user.id, 'Что-то пошло не так? Попробуй ещё раз! Введите команду заново.')


def process_city_step(message):
    """
    Функция для запроса города в котором необходимо найти отели

    :param message:
    :return: None

    Attributes:
        result (tuple): Кортеж значений user_id по пользователям, полученых от БД
        user_id (int): id пользователя
        max_price (int): Максимальная цена номера для поиска отеля
        sql_update_query (str): Запрос к БД для обновления параметра command
        msg (str): Сообщение пользователю с запросом города в котором необходимо найти отели
    """

    cursor.execute(f"SELECT user_id FROM database WHERE user_id={message.from_user.id}")
    result = cursor.fetchone()

    user_id = message.from_user.id
    user_name = message.from_user.username
    command = message.text

    if not result:
        db_table_val(
            user_id=user_id,
            user_name=user_name,
            min_price=1,
            max_price=100000,
            min_distance=0.1,
            max_distance=3.0,
            city='прага',
            hotels_count=1,
            check_in='None',
            check_out='None',
            photos_count=1,
            command=command,
            request_time=datetime.now().replace(microsecond=0)
        )
    else:
        sql_update_query = f"UPDATE database SET command = '{message.text}'," \
                           f" request_time = '{datetime.now().replace(microsecond=0)}'" \
                           f" WHERE user_id = {user_id}"
        cursor.execute(sql_update_query)
        conn.commit()

    logging.info(f'Пользователь: {user_name} - id: {user_id} - воспользовался командой: {command}')

    msg = bot.send_message(message.chat.id, 'Введите название города')

    if message.text == '/bestdeal':
        bot.register_next_step_handler(msg, price_min)
    else:
        bot.register_next_step_handler(msg, process_hotels_step)


def price_min(message):
    """
    Функция для запроса минимальной цены за номер при запросе 'bestdeal'

    :param message:
    :return: None

    Attributes:
        city (str): Город в котором необходимо найти отели
        user_id (int): id пользователя
        sql_update_query (str): Запрос к БД для обновления параметра city
        msg (str): Сообщение пользователю с запросом минимальной цены за номер
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        city = message.text.lower()
        user_id = message.from_user.id
        user_name = message.from_user.username

        logging.info(f'Пользователь: {user_name} - id: {user_id} - выбрал город: {city}')

        if city.isalpha():
            sql_update_query = f"UPDATE database SET city = '{city}' WHERE user_id = {user_id}"
            cursor.execute(sql_update_query)
            conn.commit()

            msg = bot.send_message(message.chat.id, 'Введите минимальную цену номера за сутки в рублях: ')
            bot.register_next_step_handler(msg, price_max)
        else:
            msg = bot.send_message(message.chat.id, 'Не знаю такого города, ввдете корректное название: ')
            bot.register_next_step_handler(msg, price_min)


def price_max(message):
    """
    Функция для запроса максимальной цены за номер при запросе 'bestdeal'

    :param message:
    :return: None

    Attributes:
        user_id (int): id пользователя
        min_price (int): Минимальная цена номера для поиска отеля
        sql_update_query (str): Запрос к БД для обновления параметра min_price
        msg (str): Сообщение пользователю с запросом максимальной цены за номер
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        user_id = message.from_user.id
        min_price = message.text
        user_name = message.from_user.username

        logging.info(f'Пользователь: {user_name} - id: {user_id} - задал минимальную цену: {min_price} руб.')

        if min_price.isdigit():
            sql_update_query = f"UPDATE database SET min_price = '{int(min_price)}' WHERE user_id = {user_id}"
            cursor.execute(sql_update_query)
            conn.commit()

            msg = bot.send_message(message.chat.id, 'Введите максимальную цену номера за сутки в рублях: ')
            bot.register_next_step_handler(msg, distance_min)
        else:
            msg = bot.send_message(message.chat.id, 'Ошибка при вводе! Введите минимальную цену номера (это должно быть '
                                                    'целое положительное число): ')
            bot.register_next_step_handler(msg, price_max)


def distance_min(message):
    """
    Функция для запроса минимального расстояния до центра города

    :param message:
    :return: None

    Attributes:
        user_id (int): id пользователя
        max_price (int): Максимальная цена номера для поиска отеля
        sql_update_query (str): Запрос к БД для обновления параметра max_price
        msg (str): Сообщение пользователю с запросом минимального расстояния до центра города, в котором происходит
         поиск
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        user_id = message.from_user.id
        max_price = message.text
        user_name = message.from_user.username

        logging.info(f'Пользователь: {user_name} - id: {user_id} - задал максимальную цену: {max_price} руб.')

        cursor.execute(f"SELECT min_price FROM database WHERE user_id={message.from_user.id}")
        result = cursor.fetchone()

        if max_price.isdigit() and result[0] < int(max_price):
            sql_update_query = f"UPDATE database SET max_price = '{int(max_price)}' WHERE user_id = {user_id}"
            cursor.execute(sql_update_query)
            conn.commit()

            msg = bot.send_message(message.chat.id, 'Минимальное расстояние до центра в км (Пример: 0.1)')
            bot.register_next_step_handler(msg, distance_max)
        else:
            msg = bot.send_message(message.chat.id, 'Ошибка при вводе! Введите максимальную цену номера (это должно быть '
                                                    'целое положительное число и оно должно быть больше минимальной'
                                                    ' цены): ')
            bot.register_next_step_handler(msg, distance_min)


def distance_max(message):
    """
    Функция для запроса максимального расстояния до центра города

    :param message:
    :return: None

    Attributes:
        user_id (int): id пользователя
        min_distance (float): Минимальное расстояние до центра города
        sql_update_query (str): Запрос к БД для обновления параметра min_distance
        msg (str): Сообщение пользователю с запросом максимального расстояния до центра города, в котором происходит
         поиск
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        user_id = message.from_user.id
        min_distance = message.text
        user_name = message.from_user.username

        logging.info(f'Пользователь: {user_name} - id: {user_id} - задал минимальное расстояние до центра:'
                     f' {min_distance} км.')

        try:
            if min_distance.isdigit() or float(min_distance):
                sql_update_query = f"UPDATE database SET min_distance = '{float(min_distance)}' WHERE user_id = {user_id}"
                cursor.execute(sql_update_query)
                conn.commit()

                msg = bot.send_message(message.chat.id, 'Максимальное расстояние до центра в км (Пример: 1)')
                bot.register_next_step_handler(msg, process_hotels_step)
            else:
                msg = bot.send_message(message.chat.id, 'Ошибка при вводе! введите минимальное расстояние до центра в км '
                                                        '(100 м. указывайте как 0.1, а 1 км можно указать просто 1)')
                bot.register_next_step_handler(msg, distance_max)
        except ValueError:
            msg = bot.send_message(message.chat.id, 'Вы перепутали цифру с каким-то другим символом, попробуйте ещу раз')

            bot.register_next_step_handler(msg, distance_max)


def process_hotels_step(message):
    """
    Если запрос был не 'beatdeal', то в result сохраняется название города и вызывается следующая функция.
    Если запрос был 'beatdeal', то в best_deal_list сохраняется максимальное расстояние до центра города в данном
    запросе и вызывается следующая функция.

    :param message:
    :return:

    Attributes:
        user_id (int): id пользователя
        city (str): Город в котором необходимо найти отели
        max_distance (float): Максимальное расстояние до центра города
        sql_update_query (str): Запрос к БД для обновления параметра max_distance при запросе 'bestdeal' или city, при
        запросах 'highprice' или 'lowprice'
        result (tuple): Кортеж значений command по пользователям, полученых от БД
        msg (str): Сообщение пользователю с запросом количества отелей, которое необходимой найти (не более 3)
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        user_id = message.from_user.id
        user_name = message.from_user.username

        sql_select_query = f"SELECT command FROM database WHERE user_id = {user_id}"
        cursor.execute(sql_select_query)
        result = cursor.fetchone()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons = [
            types.KeyboardButton('1'),
            types.KeyboardButton('2'),
            types.KeyboardButton('3'),
        ]
        markup.add(*buttons)

        if result[0] != '/bestdeal':
            city = message.text.lower()

            logging.info(f'Пользователь: {user_name} - id: {user_id} - выбрал город: {city}')

            if city.isalpha():
                sql_update_query = f"UPDATE database SET city = '{city}' WHERE user_id = {user_id}"
                cursor.execute(sql_update_query)
                conn.commit()

                msg = bot.send_message(message.chat.id, 'Сколько отелей Вам найти (не более 3)?', reply_markup=markup)
                bot.register_next_step_handler(msg, check_in)
            else:
                msg = bot.send_message(message.chat.id, 'Не знаю такого города, ввдете корректное название: ')
                bot.register_next_step_handler(msg, process_hotels_step)
        else:
            max_distance = message.text

            cursor.execute(f"SELECT min_distance FROM database WHERE user_id={message.from_user.id}")
            result = cursor.fetchone()

            logging.info(f'Пользователь: {user_name} - id: {user_id} - задал максимальное расстояние до центра:'
                         f' {max_distance} км.')
            try:
                if max_distance.isdigit() or float(max_distance) and float(result[0]) < float(max_distance):
                    sql_update_query = f"UPDATE database SET max_distance = '{float(max_distance)}' WHERE user_id = {user_id}"
                    cursor.execute(sql_update_query)
                    conn.commit()

                    msg = bot.send_message(message.chat.id, 'Сколько отелей Вам найти (не более 3)?', reply_markup=markup)
                    bot.register_next_step_handler(msg, check_in)
                else:
                    msg = bot.send_message(message.chat.id, 'Что-то Вы напутали при вводе, перепроверьте данные и заново'
                                                            ' введите максимальное расстояние.')
                    bot.register_next_step_handler(msg, process_hotels_step)
            except ValueError:
                msg = bot.send_message(message.chat.id, 'Вы перепутали цифру с каким-то другим символом, попробуйте'
                                                        ' ещу раз')

                bot.register_next_step_handler(msg, process_hotels_step)


def check_in(message):
    """
    У пользователя запрашивается дата заселения и сохраняется в result количество отелей которое он запросил.
    Проверка: пользователь ввёл цифру, иначе функция вызывается заново.
    Проверка: если пользователь ввел больше отелей чем можно запросить за раз, то данный пареметр устанавливается как
    максимально возможный для запроса и вызывается следующая функция.

    :param message:
    :return: None

    Attributes:
        user_id (int): id пользователя
        hotels_count (str): Количество отелей, запрашиваемое пользователем
        sql_update_query (str): Запрос к БД для обновления параметра hotels_count
        msg (str): Сообщение пользователю с об ошибке ввода количества отелей
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        user_id = message.from_user.id
        hotels_count = message.text
        user_name = message.from_user.username

        sql_select_query = f"SELECT hotels_count FROM database WHERE user_id = {user_id}"
        cursor.execute(sql_select_query)
        result = cursor.fetchone()

        if hotels_count.lower() == 'нет':
            hotels_count = result[0]
        else:
            pass

        logging.info(f'Пользователь: {user_name} - id: {user_id} - запросил {hotels_count} отелей')

        if not str(hotels_count).isdigit():
            msg = bot.send_message(message.chat.id, 'Это что за цифра такая? Давай ещё раз!')
            bot.register_next_step_handler(msg, check_in)
        else:
            if int(hotels_count) <= 3:
                sql_update_query = f"UPDATE database SET hotels_count = '{hotels_count}' WHERE user_id = {user_id}"
                cursor.execute(sql_update_query)
                conn.commit()

                calendar, step = DetailedTelegramCalendar(locale='ru', calendar_id=0, min_date=date.today()).build()
                bot.send_message(message.chat.id, 'Дата заселения', reply_markup=calendar)
                bot.register_next_step_handler(message, check_out)
            else:
                msg = bot.send_message(message.chat.id, 'Вы ввели что-то не то, давайте ещё раз!')
                bot.register_next_step_handler(msg, check_in)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=0))
def calendar1(call):
    """
    Хэндлер для функций 'check_in'

    :param call:
    :return: Дата заселения в текущем запросе

    Attributes:
        user_id (int): id пользователя
        sql_update_query (str): Запрос к БД для обновления параметра check_in (дата заселения)
    """

    user_id = call.from_user.id
    user_name = call.from_user.username

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton('Да'),
        types.KeyboardButton('Нет'),
    ]
    markup.add(*buttons)

    result_low, key, step = DetailedTelegramCalendar(locale='ru', calendar_id=0, min_date=date.today()).process(
        call.data)
    if not result_low and key:
        bot.edit_message_text('Дата', call.message.chat.id, call.message.message_id, reply_markup=key)
    elif result_low:
        bot.send_message(call.message.chat.id, f'Дата {result_low} выбрана верно?', reply_markup=markup)

    logging.info(f'Пользователь: {user_name} - id: {user_id} - выбрал дату заселения {result_low}')

    sql_update_query = f"UPDATE database SET check_in = '{result_low}' WHERE user_id = {user_id}"
    cursor.execute(sql_update_query)
    conn.commit()


def check_out(message):
    """
    У пользователя запрашивается дата отъезда

    :param message:
    :return: None
    """
    if message.text == '/restart':
        restart_function(message)
    else:
        if message.text.lower() == 'да':
            calendar, step = DetailedTelegramCalendar(locale='ru', calendar_id=1, min_date=date.today()).build()
            bot.send_message(message.chat.id, 'Дата отъезда', reply_markup=calendar)
            bot.register_next_step_handler(message, process_photos_step)
        else:
            check_in(message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def calendar2(call):
    """
    Хэндлер для функций 'check_out'

    :param call:
    :return: Дата отъезда в текущем запросе

    Attributes:
        user_id (int): id пользователя
        sql_update_query (str): Запрос к БД для обновления параметра check_out (дата отъезда)
        min_date_to_out (date): Переменная равная дате заселения + 1 день для обозначения точки отсчёта минимальной
        даты отъезда
    """

    user_id = call.from_user.id
    user_name = call.from_user.username

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        types.KeyboardButton('Да'),
        types.KeyboardButton('Нет'),
    ]
    markup.add(*buttons)

    sql_select_query = f"SELECT check_in FROM database WHERE user_id = {user_id}"
    cursor.execute(sql_select_query)
    result = cursor.fetchone()
    min_date_to_out = datetime.strptime(result[0], "%Y-%m-%d").date() + timedelta(days=1)

    result_low, key, step = DetailedTelegramCalendar(locale='ru', calendar_id=1, min_date=min_date_to_out).process(
        call.data)
    if not result_low and key:
        bot.edit_message_text('Дата', call.message.chat.id, call.message.message_id, reply_markup=key)
    elif result_low:
        bot.send_message(call.message.chat.id, f'Дата {result_low} выбрана верно?', reply_markup=markup)

        sql_select_query = f"SELECT check_in FROM database WHERE user_id = {user_id}"
        cursor.execute(sql_select_query)
        result = cursor.fetchone()

        date_format = '%Y-%m-%d'
        valid_in = datetime.strptime(result[0], date_format)
        valid_out = datetime.strptime(str(result_low), date_format)
        delta = valid_out - valid_in

        if delta.days > 0:
            sql_update_query = f"UPDATE database SET check_out = '{result_low}' WHERE user_id = {user_id}"
            cursor.execute(sql_update_query)
            conn.commit()

            logging.info(f'Пользователь: {user_name} - id: {user_id} - выбрал дату отъезда {result_low}')
        else:
            bot.send_message(call.message.chat.id, 'Вы ввели дату отъяезда раньше даты заселения, измените дату '
                                                   'отъезда.')
            check_out(call.message)


def process_photos_step(message):
    """
    Запрос у пользователя на поиск фотографий к отелям

    :param message:
    :return: None
    """
    if message.text == '/restart':
        restart_function(message)
    else:
        if message.text.lower() == 'да':
            buttons = [
                types.InlineKeyboardButton(text='Да', callback_data='yes'),
                types.InlineKeyboardButton(text='Нет', callback_data='no'),
                types.InlineKeyboardButton(text='Перезапустить', callback_data='restart')
            ]
            markup = types.InlineKeyboardMarkup(row_width=3)
            markup.add(*buttons)
            bot.send_message(message.chat.id, text='Показать фотки или пусть будет сюрпризом?', reply_markup=markup)
        else:
            check_out(message)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    """
    Запись ответа пользователя в result из предыдущего шага.
    Запрос количества фотографий, если на предыдущем шаге выбрали 'да' и вызов соответствующей функции.
    Если на предыдущем шаге выбрано 'нет', то вызывается функция поиска и вывода данных без фотографий.

    :param call:
    :return: None

    Attributes:
        user_id (int): id пользователя
        sql_select_query (str): Запрос к БД для получения кортежа с коммандой данного пользователя
        result (tuple): Кортеж с коммандой, введённой пользователем
        msg_pic (str): Сообщение пользователю с запросом количества фотографий, необходимых для вывода (не более 3)
    """

    if call.data == 'restart':
        restart_function(call)
    else:
        user_id = call.from_user.id
        user_name = call.from_user.username

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        buttons = [
            types.KeyboardButton('1'),
            types.KeyboardButton('2'),
            types.KeyboardButton('3'),
        ]
        markup.add(*buttons)

        sql_select_query = f"SELECT command FROM database WHERE user_id = {user_id}"
        cursor.execute(sql_select_query)
        result = cursor.fetchall()

        if call.data == 'yes':
            logging.info(f'Пользователь: {user_name} - id: {user_id} - запросил вывод результата с фотографиями')
            msg_pic = bot.send_message(call.message.chat.id, 'Сколько фотографий показать (не больше 3)?',
                                       reply_markup=markup)
            bot.register_next_step_handler(msg_pic, photos_count_step)
        elif call.data == 'no':
            logging.info(f'Пользователь: {user_name} - id: {user_id} - запросил вывод результата без фотографий')

            if result[0][0] == "/lowprice":
                answer = 'no'
                get_data_low(call, answer)
            elif result[0][0] == "/highprice":
                answer = 'no'
                get_data_high(call, answer)
            elif result[0][0] == "/bestdeal":
                answer = 'no'
                get_data_best(call, answer)

        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


def photos_count_step(message):
    """
    Сохранение количества запрашиваемых фотографий в данном запросе в result
    Проверка: в зависимости от введённой пользователем команды вызывается необходимая функция.

    :param message:
    :return: None

    Attributes:
        user_id (int): id пользователя
        photos_count (int): Количество фотографий для отправки пользователю
        sql_select_query (str): Запрос к БД для получения кортежа с коммандой данного пользователя
        sql_update_query (str): Запрос к БД для обновления параметра photos_count (количество фотографий)
    """

    if message.text == '/restart':
        restart_function(message)
    else:
        user_id = message.from_user.id
        photos_count = message.text
        user_name = message.from_user.username

        if photos_count.isdigit() and int(photos_count) <= 3:
            logging.info(f'Пользователь: {user_name} - id: {user_id} - запросил вывод {photos_count} фотографий')

            sql_update_query = f"UPDATE database SET photos_count = '{int(photos_count)}' WHERE user_id = {user_id}"
            cursor.execute(sql_update_query)
            conn.commit()
        else:
            msg = bot.send_message(message.chat.id, 'Вы ввели что-то не то, давайте ещё раз!')
            bot.register_next_step_handler(msg, photos_count_step)

        sql_select_query = f"SELECT command FROM database WHERE user_id = {user_id}"
        cursor.execute(sql_select_query)
        result = cursor.fetchall()

        if result[0][0] == "/lowprice":
            answer = 'yes'
            get_data_low(message, answer)
        elif result[0][0] == "/highprice":
            answer = 'yes'
            get_data_high(message, answer)
        elif result[0][0] == "/bestdeal":
            answer = 'yes'
            get_data_best(message, answer)
