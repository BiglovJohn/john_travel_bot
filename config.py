import telebot
import os
from dotenv import load_dotenv

"""
Файл с ключами

API_TOKEN (str): Токен для Rapid API
bot (class): Инициализация бота с помощью токена SECRET_TOKEN
"""

load_dotenv()

bot = telebot.TeleBot(os.getenv('KEY'))

headers = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': os.getenv('API_TOKEN_1') # API_TOKEN_2, API_TOKEN_1
}

url = "https://hotels4.p.rapidapi.com/properties/list"
url2 = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
url3 = "https://hotels4.p.rapidapi.com/locations/search"
