import sqlite3
from datetime import datetime


conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

sql_create_query = ("""CREATE TABLE IF NOT EXISTS database(
id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
user_id INTEGER NOT NULL UNIQUE,
user_name TEXT,
min_price INTEGER DEFAULT (1),
max_price INTEGER DEFAULT (100000),
min_distance REAL DEFAULT (0.1),
max_distance REAL DEFAULT (3.0),
city TEXT NOT NULL DEFAULT прага,
hotels_count INTEGER DEFAULT (1),
check_in VARCHAR,
check_out VARCHAR,
photos_count INTEGER,
command VARCHAR NOT NULL,
request_time DATETIME DEFAULT ( (DATE('now', 'localtime') ) ) )
""")

sql_create_query_history = ("""CREATE TABLE IF NOT EXISTS hotels_result_db (
user_id INTEGER,
req_time DATETIME NOT NULL,
hotel_name VARCHAR (250) NOT NULL,
hotel_address VARCHAR (250),
distance_to_center VARCHAR (250),
price_per_night VARCHAR (250),
total_price VARCHAR (250) )
""")

cursor.execute(sql_create_query)
cursor.execute(sql_create_query_history)
conn.commit()


def db_table_val(
        user_id: int,
        user_name: str,
        min_price: int,
        max_price: int,
        min_distance: float,
        max_distance: float,
        city: str,
        hotels_count: int,
        check_in,
        check_out,
        photos_count: int,
        command: str,
        request_time: datetime
):
    """
    Функция записывает параметры в БД, которые бот получает от пользователя

    :param user_id: id пользователя
    :param user_name: Имя пользователя
    :param min_price: Минимальная цена за номер
    :param max_price: Максимальная цена за номер
    :param min_distance: Минимальная дистанция от центра города
    :param max_distance: Максимальная дистанция от центра города
    :param city: Запрашиваемый город
    :param hotels_count: Запрашиваемое количество отелей
    :param check_in: Дата заселения
    :param check_out: Дата выезда
    :param photos_count: Количество фотографий в запросе
    :param command: Команда запроса
    :param request_time: Время запроса
    :return: None
    """

    cursor.execute('INSERT INTO database ('
                   'user_id,'
                   'user_name,'
                   'min_price,'
                   'max_price,'
                   'min_distance,'
                   'max_distance,'
                   'city,'
                   'hotels_count,'
                   'check_in,'
                   'check_out,'
                   'photos_count,'
                   'command,'
                   'request_time)'
                   ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (
                       user_id,
                       user_name,
                       min_price,
                       max_price,
                       min_distance,
                       max_distance,
                       city,
                       hotels_count,
                       check_in,
                       check_out,
                       photos_count,
                       command,
                       request_time
                   )
                   )
    conn.commit()


def hotels_results(
        user_id: int,
        req_time: datetime,
        hotel_name: str,
        hotel_address: str,
        distance_to_center: str,
        price_per_night: str,
        total_price: str,
        command: str,
):
    """
    Функция записывает данные для последующего вывода при запросе полельзователем комманды /history

    :param command: Команда, которую отправил пользователь
    :param user_id: id пользователя
    :param req_time: Время запроса
    :param hotel_name: Название отеля
    :param hotel_address: Адрес отеля
    :param distance_to_center: Расстояние до центра города
    :param price_per_night: Цена за ночь
    :param total_price: Общая стоимость за выбраный период
    :return: None
    """

    cursor.execute('INSERT INTO hotels_result_db ('
                   'user_id,'
                   'req_time,'
                   'hotel_name,'
                   'hotel_address,'
                   'distance_to_center, '
                   'price_per_night,'
                   'total_price,'
                   'command)'
                   'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (
                       user_id,
                       req_time,
                       hotel_name,
                       hotel_address,
                       distance_to_center,
                       price_per_night,
                       total_price,
                       command
                   )
                   )
    conn.commit()
