import telebot

from botrequests import data_request, default_commands, history_requst
from config import bot


@bot.message_handler(commands=["start"])
def start_message(message: telebot.types.Message) -> None:
    default_commands.start_message(message)


@bot.message_handler(commands=["help"])
def start_message(message: telebot.types.Message) -> None:
    default_commands.help_message(message)


@bot.message_handler(commands=["lowprice"])
def low_price_start_message(message: telebot.types.Message) -> None:
    data_request.process_city_step(message)


@bot.message_handler(commands=["highprice"])
def high_price_start_message(message: telebot.types.Message) -> None:
    data_request.process_city_step(message)


@bot.message_handler(commands=["bestdeal"])
def bestdeal_start(message: telebot.types.Message) -> None:
    data_request.process_city_step(message)


@bot.message_handler(commands=["history"])
def history_start(message: telebot.types.Message) -> None:
    history_requst.process_history_request(message)


if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as ex:
        print(ex)
