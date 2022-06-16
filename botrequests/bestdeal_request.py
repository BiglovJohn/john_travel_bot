import datetime

import requests
import json

from telebot.types import InputMediaPhoto
from config import bot, headers, url, url2, url3
from db import hotels_results, cursor


def get_data_best(message, answer: str):
    """
    Функция для получения ответа от API на запрос 'bestdeal' с фотографиями

    :param message: Передаётся класс Message библиотеки TelegramBotAPI
    :param answer: Ответ пользователя показывать фотографии отеля или нет
    :return: result_low

    city (str): Переменной присваивается название города по которому будет происходить поиск отелей
    hotels_count (int): Переменной присваивается значение количества городов из ответов пользователя
    h_iter (int): Счётчик итераций при поиске отелей, соответствующих параметрам запроса
    pic_count (int): Количество фотографий для вывода пользователю
    min_price (str): Минимальная цена за номер в формате строки для передачи в запрос к API
    max_price (str): Максимальная цена за номер в формате строки для передачи в запрос к API
    min_distance (float): Минимальное расстояние до центра города заданное пользователем и переведенное в мили для API
    max_distance (float): Максимальное расстояние до центра города заданное пользователем и переведенное в мили для API
    url (str): Адрес для получения основных параметров от API
    url2 (str): Адрес для получения фотографий от API
    url3 (str): Адрес для получения id города для последующей передачи в запрос к API
    querystring_city (dict): Словарь параметров, передаваемых в запрос к API, для получения запрашиваемого города
    response_city (request): Ответ от API по переданым параметрам querystring_city
    data_city (json): Десериализация полученных данных в response_city в формате JSON
    city_id (str): id запрашиваемого пользователем города
    querystring_low (dict):  Словарь параметров, передаваемых в запрос к API, для получения запрашиваемых данных
    response_low (request): Ответ от API по переданым параметрам querystring_low
    data_low (json): Десериализация полученных данных в response_low в формате JSON
    """

    user_id = message.from_user.id
    sql_select_query = f"SELECT * FROM database WHERE user_id = {user_id}"
    cursor.execute(sql_select_query)
    result = cursor.fetchone()

    city = result[7]
    min_price = result[3]
    max_price = result[4]
    check_in = result[9]
    check_out = result[10]
    h_iter = 0

    querystring_city = {"query": city, "locale": "ru_RU"}
    response_city = requests.request("GET", url3, headers=headers, params=querystring_city)
    data_city = json.loads(response_city.text)

    try:
        city_id = data_city['suggestions'][0]['entities'][0]['destinationId']
    except Exception as ex:
        print(ex)
        city_id = '1634829'
        bot.send_message(message.chat.id, 'Я не нашёл нужный город, поэтому выдам тебе результат по Праге')

    querystring_low = {"destinationId": city_id,
                       "pageNumber": "1",
                       "pageSize": "25",
                       "checkIn": check_in,
                       "checkOut": check_out,
                       "adults1": "1",
                       "priceMin": min_price,
                       "priceMax": max_price,
                       "sortOrder": "DISTANCE_FROM_LANDMARK",
                       "locale": "en_EN",
                       "currency": "RUB",
                       "landmarkIds": "City center"
                       }
    response_best = requests.request("GET", url, headers=headers, params=querystring_low)
    data_best = json.loads(response_best.text)

    data = data_best['data']['body']['searchResults']['results']

    if answer == 'yes':
        searching_func_pic(message, user_id, data, url2, h_iter)
    else:
        searching_func(message, user_id, data, h_iter)


def searching_func_pic(message, user_id, data, pic_url, func_iter: int):
    """
    Функция сбора данных из API по заданным параметрам

    func_count (int): Передаётся значение параметра h_count
    func_iter (int): Передаётся значение параметра h_iter
    :return: result_low

    distance (float): Значение расстояния до центра города для каждого из отелей
    current_hotel_id (str): id текущего проверяемого отеля
    hotel_name (str): Название отеля
    address (str): Адрес отеля
    distance_to_center (str): Расстояние до центра города от данного отеля
    price (str): Цена за ночь
    total_price (str): Общая стоимость за выбранный период
    """

    sql_select_query = f"SELECT * FROM database WHERE user_id = {user_id}"
    cursor.execute(sql_select_query)
    result = cursor.fetchone()

    hotels_count = result[8]
    pic_count = result[11]
    min_distance = result[5] * 0.62
    max_distance = result[6] * 0.62
    check_in = result[9]
    check_out = result[10]
    command = result[12]
    request_time = result[13]

    date_obj_1 = datetime.datetime.strptime(check_in, '%Y-%m-%d')
    date_obj_2 = datetime.datetime.strptime(check_out, '%Y-%m-%d')
    delta = (date_obj_2 - date_obj_1).days

    while func_iter != hotels_count:
        distance = float(data[func_iter]['landmarks'][0]['distance'].split(' ')[0])
        if min_distance <= distance <= max_distance:
            hotel_id = data[func_iter]['id']
            hotel_name = data[func_iter]['name']
            try:
                address = data[func_iter]['address']['streetAddress']
            except KeyError:
                address = data[func_iter]['address']['region']
            dist_to_center = (data[func_iter]['landmarks'][0]['distance']).split(' ')[0]
            price = (data[func_iter]['ratePlan']['price']["current"]).split(' ')[0]
            try:
                total_price = (data[func_iter]['ratePlan']['price']['fullyBundledPricePerStay']).split(' ')
            except KeyError:
                total_price = price * delta

            """ Переменные для передачи значений в БД """

            hotels_results(
                user_id=message.from_user.id,
                req_time=request_time,
                hotel_name=hotel_name,
                hotel_address=address,
                distance_to_center=dist_to_center,
                price_per_night=price.replace(',', '.'),
                total_price=total_price[1].replace(',', '.'),
                command=command
            )

            querystring_pic = {"id": hotel_id}
            response_pic = requests.request("GET", pic_url, headers=headers, params=querystring_pic)
            data_pic = json.loads(response_pic.text)

            media_group = []
            for i in range(pic_count):
                """
                Получение фотографий отелей

                querystring_pic (dict): Словарь параметров, передаваемых в запрос к API, для получения фото
                response_pic (request): Ответ от API
                data_pic (json): Десериализация полученных данных в response_pic в формате JSON
                pic_url (str): Ссылка на картинку
                """

                picture_url = (data_pic['hotelImages'][i]['baseUrl']).format(size='z')
                media_group.append(InputMediaPhoto(picture_url, caption=''))

            bot.send_media_group(chat_id=message.chat.id, media=media_group)

            result_low = (
                'Название: {hotel}\nАдрес: {adress}\nРасстояние до центра: {city_center} км.\n'
                'Цена за ночь: {price} РУБ\nИтого: {total_price} РУБ\nСсылка на отель: {link}'.format(
                    hotel=hotel_name,
                    adress=address,
                    city_center=round((float(dist_to_center) / 0.62), 2),
                    price=price.replace(',', '.'),
                    total_price=total_price[1].replace(',', '.'),
                    link='https://www.hotels.com/ho' + str(hotel_id)
                )
            )
            func_iter += 1
            bot.send_message(message.chat.id, result_low, disable_web_page_preview=True)
        else:
            searching_func_pic(message, user_id, data, pic_url, func_iter)


def searching_func(message, user_id, data, func_iter: int):
    """
    Функция сбора данных из API по заданным параметрам

    func_count (int): Передаётся значение параметра h_count
    func_iter (int): Передаётся значение параметра h_iter
    :return: result_low

    distance (float): Значение расстояния до центра города для каждого из отелей
    current_hotel_id (str): id текущего проверяемого отеля
    hotel_name (str): Название отеля
    address (str): Адрес отеля
    distance_to_center (str): Расстояние до центра города от данного отеля
    price (str): Цена за ночь
    total_price (str): Общая стоимость за выбранный период
    """

    sql_select_query = f"SELECT * FROM database WHERE user_id = {user_id}"
    cursor.execute(sql_select_query)
    result = cursor.fetchone()

    hotels_count = result[8]
    min_distance = result[5] * 0.62
    max_distance = result[6] * 0.62
    request_time = result[13]
    check_in = result[9]
    check_out = result[10]
    command = result[12]

    date_obj_1 = datetime.datetime.strptime(check_in, '%Y-%m-%d')
    date_obj_2 = datetime.datetime.strptime(check_out, '%Y-%m-%d')
    delta = (date_obj_2 - date_obj_1).days

    while func_iter != hotels_count:
        distance = float(data[func_iter]['landmarks'][0]['distance'].split(' ')[0])

        if min_distance <= distance <= max_distance:
            hotel_name = data[func_iter]['name']
            hotel_id = data[func_iter]['id']
            try:
                address = data[func_iter]['address']['streetAddress']
            except KeyError:
                address = data[func_iter]['address']['region']
            dist_to_center = (data[func_iter]['landmarks'][0]['distance']).split(' ')[0]
            price = (data[func_iter]['ratePlan']['price']["current"]).split(' ')[0]
            try:
                total_price = (data[func_iter]['ratePlan']['price']['fullyBundledPricePerStay']).split(' ')
            except KeyError:
                total_price = price * delta

            """ Переменные для передачи значений в БД """

            h_name = str(hotel_name)
            h_address = str(address)

            hotels_results(
                user_id=message.from_user.id,
                req_time=request_time,
                hotel_name=h_name,
                hotel_address=h_address,
                distance_to_center=dist_to_center,
                price_per_night=price.replace(',', '.'),
                total_price=str(total_price[1].replace(',', '.')),
                command=command
            )

            result_low = (
                'Название: {hotel}\nАдрес: {adress}\nРасстояние до центра: {city_center} км.\n'
                'Цена за ночь: {price} РУБ\nИтого: {total_price} РУБ\nСсылка на отель: {link}'.format(
                    hotel=hotel_name,
                    adress=address,
                    city_center=round((float(dist_to_center) / 0.62), 2),
                    price=price.replace(',', '.'),
                    total_price=total_price[1].replace(',', '.'),
                    link='https://www.hotels.com/ho' + str(hotel_id)
                )
            )
            func_iter += 1
            bot.send_message(message.message.chat.id, result_low, disable_web_page_preview=True)
        else:
            searching_func(message, user_id, data, func_iter)
