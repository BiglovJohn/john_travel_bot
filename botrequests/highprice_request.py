import datetime

import requests
import json

from telebot.types import InputMediaPhoto
from config import bot, headers, url, url2, url3
from db import hotels_results, cursor


def get_data_high(message, answer: str):
    """
    Функция для получения ответа от API на запрос 'highprice' с фотографиями

    :param answer: Ответ пользователя показывать фотографии отеля или нет
    :param message: Передаётся класс Message библиотеки TelegramBotAPI
    :return: result_high

    city_h (str): Переменной присваивается название города по которому будет происходить поиск отелей
    hotels_count (int): Переменной присваивается значение количества городов из ответов пользователя
    pic_count (int): Количество фотографий для вывода пользователю
    min_price (str): Минимальная цена за номер в формате строки для передачи в запрос к API
    max_price (str): Максимальная цена за номер в формате строки для передачи в запрос к API
    min_distance (float): Минимальное расстояние до центра города заданное пользователем
    max_distance (float): Максимальное расстояние до центра города заданное пользователем
    url (str): Адрес для получения основных параметров от API
    url2 (str): Адрес для получения фотографий от API
    url3 (str): Адрес для получения id города для последующей передачи в запрос к API
    querystring_city (dict): Словарь параметров, передаваемых в запрос к API, для получения запрашиваемого города
    response_city (request): Ответ от API по переданым параметрам querystring_city
    data_city (json): Десериализация полученных данных в response_city в формате JSON
    current_destination_id (str): id запрашиваемого пользователем города
    querystring_high (dict):  Словарь параметров, передаваемых в запрос к API, для получения запрашиваемых данных
    response_high (request): Ответ от API по переданым параметрам querystring_high
    data_high (json): Десериализация полученных данных в response_high в формате JSON
    distance (float): Значение расстояния до центра города для каждого из отелей
    current_hotel_id (str): id текущего проверяемого отеля
    hotel_name (str): Название отеля
    address (str): Адрес отеля
    distance_to_center (str): Расстояние до центра города от данного отеля
    price (str): Цена за ночь
    total_price (str): Общая стоимость за выбранный период
    """

    user_id = message.from_user.id
    sql_select_query = f"SELECT * FROM database WHERE user_id = {user_id}"
    cursor.execute(sql_select_query)
    result = cursor.fetchone()

    city = result[7]
    hotels_count = result[8]
    pic_count = result[11]
    check_in = result[9]
    check_out = result[10]
    command = result[12]
    request_time = result[13]

    date_obj_1 = datetime.datetime.strptime(check_in, '%Y-%m-%d')
    date_obj_2 = datetime.datetime.strptime(check_out, '%Y-%m-%d')
    delta = (date_obj_2 - date_obj_1).days

    querystring_city = {"query": city, "locale": "ru_RU"}
    response_city = requests.request("GET", url3, headers=headers, params=querystring_city)
    data_city = json.loads(response_city.text)

    try:
        city_id = data_city['suggestions'][0]['entities'][0]['destinationId']
    except Exception as ex:
        print(ex)
        city_id = '1634829'
        bot.send_message(message.chat.id, 'Я не нашёл нужный город, поэтому выдам тебе результат по Праге')

    querystring_high = {
        "destinationId": city_id,
        "pageNumber": "1",
        "pageSize": "25",
        "checkIn": check_in,
        "checkOut": check_out,
        "adults1": "1",
        "sortOrder": "PRICE_HIGHEST_FIRST",
        "locale": "en_EN",
        "currency": "RUB"
    }

    response_high = requests.request("GET", url, headers=headers, params=querystring_high)
    data_high = json.loads(response_high.text)
    data = data_high['data']['body']['searchResults']['results']

    if answer == 'yes':
        for i in range(hotels_count):
            hotel_id = data[i]['id']
            hotel_name = data[i]['name']
            try:
                address = data[i]['address']['streetAddress']
            except KeyError:
                address = data[i]['address']['region']
            dist_to_center = (data[i]['landmarks'][0]['distance']).split(' ')[0]
            price = (data[i]['ratePlan']['price']["current"]).split(' ')[0]
            try:
                total_price = (data[i]['ratePlan']['price']['fullyBundledPricePerStay']).split(' ')[1]
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
                total_price=total_price.replace(',', '.'),
                command=command
            )

            media_group = []
            querystring_pic = {"id": hotel_id}
            response_pic = requests.request("GET", url2, headers=headers, params=querystring_pic)
            data_pic = json.loads(response_pic.text)

            for j in range(pic_count):
                """
                Получение фотографий отелей
    
                querystring_pic (dict): Словарь параметров, передаваемых в запрос к API, для получения фото
                response_pic (request): Ответ от API
                data_pic (json): Десериализация полученных данных в response_pic в формате JSON
                pic_url (str): Ссылка на картинку
                """

                pic_url = (data_pic['hotelImages'][j]['baseUrl']).format(size='z')
                media_group.append(InputMediaPhoto(pic_url, caption=''))
            bot.send_media_group(chat_id=message.chat.id, media=media_group)

            result_high = (
                'Название: {hotel}\nАдрес: {adress}\nРасстояние до центра: {city_center} км.\nЦена за ночь:'
                ' {price} РУБ\nИтого: {total_price} РУБ\nСсылка на отель: {link}'.format(
                    hotel=hotel_name,
                    adress=address,
                    city_center=round((float(dist_to_center) / 0.62), 2),
                    price=price.replace(',', '.'),
                    total_price=total_price.replace(',', '.'),
                    link='https://www.hotels.com/ho' + str(hotel_id)
                )
            )

            bot.send_message(message.chat.id, result_high, disable_web_page_preview=True)
    else:
        for i in range(hotels_count):
            current_hotel_id = data[i]['id']
            hotel_name = data[i]['name']
            try:
                address = data[i]['address']['streetAddress']
            except KeyError:
                address = data[i]['address']['region']
            dist_to_center = (data[i]['landmarks'][0]['distance']).split(' ')[0]
            price = (data[i]['ratePlan']['price']["current"]).split(' ')[0]
            try:
                total_price = (data[i]['ratePlan']['price']['fullyBundledPricePerStay']).split(' ')[1]
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
                total_price=total_price.replace(',', '.'),
                command=command
            )

            result_high = (
                'Название: {hotel}\nАдрес: {adress}\nРасстояние до центра: {city_center} км.\nЦена за ночь:'
                ' {price} РУБ\nИтого: {total_price} РУБ\nСсылка на отель: {link}'.format(
                    hotel=hotel_name,
                    adress=address,
                    city_center=round((float(dist_to_center) / 0.62), 2),
                    price=price.replace(',', '.'),
                    total_price=total_price.replace(',', '.'),
                    link='https://www.hotels.com/ho' + str(current_hotel_id)
                )
            )

            bot.send_message(message.message.chat.id, result_high, disable_web_page_preview=True)
