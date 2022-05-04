from config import bot


@bot.message_handler(commands=['start'])
def start_message(message):
    sti = open('welcome.tgs', 'rb')
    bot.send_sticker(message.chat.id, sti)
    bot.send_message(message.chat.id,
                     'Добро пожаловать {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы '
                     'помочь тебе выбрать лучший отель для твоего отпуска!\nЯ помогу тебе освоиться, просто введи '
                     '"/help"'.format(message.from_user, bot.get_me()), parse_mode='html')


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id,
                     'Я заранее подготовил несколько вариантов запросов! Ты можешь воспользоваться'
                     ' ими в меню слева (это там где стикеры).')
