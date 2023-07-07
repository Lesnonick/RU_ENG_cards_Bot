from telebot import TeleBot, types
import random
from Settings import Settings, Command, Replies
import DB_Cards
import Dict_uploader
from Cards_logger import cards_logger


bot = TeleBot(Settings.API_TOKEN)


@bot.message_handler(func=lambda message: message.text == Command.MENU)
def default_position(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=4)
    buttons = [Command.HELP, Command.LIST, Command.CARDS, Command.CLEAN, Command.ADD_WORD, Command.DELETE_WORD]
    markup.add(*buttons)
    bot.send_message(chat_id, 'Выберите следующее действие.', reply_markup=markup)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    first_name = message.chat.first_name
    chat_id = message.chat.id
    bot.send_message(chat_id, f'Идет добавление 12 слов ...')
    cards_logger.info(f'id{chat_id}: начал работать с Ботом и/или добавляет 12 дефолтных слов.')
    db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
    db.initial_data(first_name)
    bot.send_message(chat_id, f'Добро пожаловать на курсы изучения английского языка, {first_name}\n')
    default_position(message)


@bot.message_handler(commands=['help'])
def send_help(message):
    chat_id = message.chat.id
    first_name = message.chat.first_name
    bot.send_message(chat_id, f'Добро пожаловать в Бот, предназначенный для изучения английских слов, '
                              f'{first_name}! В разделе /help можно ознакомиться с его основными функциями\n\n'
                              f'/start - загрузка первых 12 слов с переводами и примером английского использования '
                              f'для ознакомления с Ботом\n'
                              f'/list - вывод списка изучаемых слов на русском и английском языке '
                              f'в алфавитном порядке\n'
                              f'/cards - начало изучения слов из Вашего списка изучаемых слов\n'
                              f'/clean - удаляет все слова из Вашего списка изучаемых слов\n\n'
                              f'Для выполнения следующих действий необходимо написать в чат сообщение:\n'
                              f'*{Command.ADD_WORD}* - позволяет добавить слово в Ваш список\n'
                              f'*{Command.DELETE_WORD}* - позволяеть удалить слово из Вашего списка',
                     parse_mode='markdown')
    cards_logger.info(f'id{chat_id}: запросил /help и получил информацию.')
    default_position(message)


@bot.message_handler(commands=['list'])
def list_word_reply(message):
    chat_id = message.chat.id
    db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
    words_num = db.words_num()
    if words_num < 1:
        bot.send_message(chat_id, 'Ваш список пуст.\nДобавьте слова с помощью соответствующей функции (см. /help).')
        cards_logger.info(f'id{chat_id}: получил информацию о списке слов. Его список пуст.')
        return []
    else:
        words = db.list_words()
        list_reply = ''
        for word in words:
            list_reply += f'{word[0]}. {word[1]}   ---   {word[2]}\n'
        bot.send_message(chat_id, list_reply)
        cards_logger.info(f'id{chat_id}: получил информацию о списке слов.')
        return words


@bot.message_handler(commands=['clean'])
def clean_list(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=1)
    yes_button = types.KeyboardButton(Command.YES)
    menu_button = types.KeyboardButton(Command.MENU)
    buttons = [yes_button, menu_button]
    markup.add(*buttons)
    bot.send_message(chat_id, 'Вы уверены, что хотите очистить свой список?', reply_markup=markup)
    cards_logger.info(f'id{chat_id}: запросил удаление списка слов.')
    bot.register_next_step_handler(message, clean_proved)


def clean_proved(message):
    if message.text == Command.YES:
        chat_id = message.chat.id
        db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
        words = db.list_words()
        for word in words:
            db.delete_word(word[1])
        cards_logger.info(f'id{chat_id}: подтвердил удаление списка слов. Список теперь пуст.')
        bot.send_message(chat_id, 'Ваш список пуст, милорд')
    default_position(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Введите слово на русском языке', reply_markup=types.ReplyKeyboardRemove())
    cards_logger.info(f'id{chat_id}: запросил добавление нового слова в список.')
    bot.register_next_step_handler(message, get_word_auto)


def get_word_auto(message):
    chat_id = message.chat.id
    rus_word = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    translate, usage = Dict_uploader.get_translate_and_example(rus_word)
    answers = [Command.YES, Command.CHANGE_ALL, Command.CHANGE_USAGE, Command.CANCEL]
    words_buttons = [types.KeyboardButton(answer) for answer in answers]
    markup.add(*words_buttons)
    bot.send_message(chat_id, f'Перевод: {translate}\nПример использования: {usage}', reply_markup=markup)
    bot.register_next_step_handler(message, change_translate, rus_word, translate, usage)


def change_translate(message, rus_word, translate, usage):
    chat_id = message.chat.id
    if message.text == Command.YES:
        cards_logger.info(f'id{chat_id}: согласился с предложенным вариантом перевода '
                          f'и использования "{rus_word}".')
        first_name = message.chat.first_name
        db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
        init_words_num = db.words_num()
        db.add_word(rus_word, translate, usage, first_name)
        words_num = db.words_num()
        if init_words_num == words_num:
            bot.send_message(chat_id, 'Слово не добавлено, так как в Вашем списке уже есть карточка с этим словом.\n'
                                      'Чтобы убедиться, посмотрите /list.')
        else:
            bot.send_message(chat_id, Replies.WORD_ADDED)
            cards_logger.info(f'id{chat_id}: добавил слово "{rus_word}" в список.')
        bot.send_message(chat_id, Replies.NUM_WORD + str(words_num))
        default_position(message)
    elif message.text == Command.CHANGE_ALL:
        bot.send_message(chat_id, 'Введите перевод', reply_markup=types.ReplyKeyboardRemove())
        cards_logger.info(f'id{chat_id}: запросил изменение предложенных перевода '
                          f'и применения для "{rus_word}".')
        bot.register_next_step_handler(message, add_translate, rus_word)
    elif message.text == Command.CHANGE_USAGE:
        bot.send_message(chat_id, 'Введите пример использования', reply_markup=types.ReplyKeyboardRemove())
        cards_logger.info(f'id{chat_id}: запросил изменение предложенного применения для "{rus_word}".')
        bot.register_next_step_handler(message, add_usage, rus_word, translate)
    else:
        bot.send_message(chat_id, Replies.ADD_CANCELED)
        cards_logger.info(f'id{chat_id}: отменил добавление слова "{rus_word}".')
        default_position(message)


def add_translate(message, rus_word):
    chat_id = message.chat.id
    if message.text == Command.CANCEL:
        bot.send_message(chat_id, Replies.ADD_CANCELED)
        cards_logger.info(f'id{chat_id}: отменил добавление слова "{rus_word}".')
        default_position(message)
    else:
        translate = message.text
        bot.send_message(chat_id, 'Введите пример использования', reply_markup=types.ReplyKeyboardRemove())
        cards_logger.info(f'id{chat_id}: уточнил перевод слова "{rus_word}" и изменяет применение.')
        bot.register_next_step_handler(message, add_usage, rus_word, translate)


def add_usage(message, rus_word, translate):
    chat_id = message.chat.id
    if message.text == Command.CANCEL:
        bot.send_message(chat_id, Replies.ADD_CANCELED)
        cards_logger.info(f'id{chat_id}: отменил добавление слова "{rus_word}".')
    else:
        first_name = message.chat.first_name
        usage = message.text
        db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
        init_words_num = db.words_num()
        db.add_word(rus_word, translate, usage, first_name)
        words_num = db.words_num()
        if init_words_num == words_num:
            bot.send_message(chat_id, 'Слово не добавлено, так как в Вашем списке уже есть карточка с этим словом.\n'
                                      'Чтобы убедиться, посмотрите /list.')
        else:
            bot.send_message(chat_id, Replies.WORD_ADDED)
            cards_logger.info(f'id{chat_id}: добавил слово "{rus_word}" в список.')
        words_num = db.words_num()
        bot.send_message(chat_id, Replies.NUM_WORD + str(words_num))
    default_position(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def select_word_to_delete(message):
    chat_id = message.chat.id
    words = list_word_reply(message)
    if len(words) == 0:
        bot.send_message(chat_id, 'Удалять нечего.\nДобавьте слова с помощью соответствующей функции (см. /help).')
        cards_logger.info(f'id{chat_id}: запросил удаление слова из пустого списка.')
        default_position(message)
    else:
        bot.send_message(chat_id, 'Напишите *НОМЕР* слова, которое хотите удалить', parse_mode='markdown',
                         reply_markup=types.ReplyKeyboardRemove())
        cards_logger.info(f'id{chat_id}: запросил удаление слова из списка.')
        bot.register_next_step_handler(message, delete_word, words)


def delete_word(message, words):
    chat_id = message.chat.id
    num = message.text
    len_list = len(words)
    if num.isdigit() and int(num) <= len_list:
        words_list = dict()
        for word in words:
            words_list[word[0]] = word[1]
        db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
        rus_word = words_list[int(num)]
        db.delete_word(rus_word)
        bot.send_message(chat_id, 'Слово удалено! ✔')
        cards_logger.info(f'id{chat_id}: удалил слово "{rus_word}" из списка.')
        words_num = db.words_num()
        bot.send_message(chat_id, Replies.NUM_WORD + str(words_num))
    else:
        bot.send_message(chat_id, f'Такого номера не существует в Вашем списке.\nВыполните операцию заново. 🔄')
        cards_logger.info(f'id{chat_id}: указал несуществующий номер слова. Удаление отменено.')
    default_position(message)


@bot.message_handler(commands=['cards'])
def show_cards(message):
    chat_id = message.chat.id
    db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
    num_word = len(db.list_words())
    if num_word < 4:
        bot.send_message(chat_id, 'Количество слов в Вашем списке меньше 4. '
                                  'Добавьте слова с помощью соответствующей функции (см. /help).')
        cards_logger.warning(f'id{chat_id}: пытался начать работу с карточками с {num_word} слов(-ами/-ом).')
        default_position(message)
    else:
        if message.text == Command.MENU:
            cards_logger.info(f'id{chat_id}: прекратил тренировку и перешёл в меню Бота.')
            default_position(message)
        else:
            rus_word, translate, wrong_words, usage = db.select_rand_word()
            bot.reply_to(message, f"Переведи слово\n 🇷🇺 {rus_word}")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            words = wrong_words + [translate]
            random.shuffle(words)
            buttons = [types.KeyboardButton(word) for word in words]
            add_word_button = types.KeyboardButton(Command.ADD_WORD)
            miss_button = types.KeyboardButton(Command.MISS)
            menu_button = types.KeyboardButton(Command.MENU)
            buttons.extend([add_word_button, miss_button, menu_button])
            markup.add(*buttons)
            bot.send_message(message.chat.id, 'Выберите верный перевод:', reply_markup=markup)
            cards_logger.info(f'id{chat_id}: пытается угадать слово "{rus_word}"\n'
                              f'из вариантов {words} (верно {translate})')
            bot.register_next_step_handler(message, reply, translate, usage)


def reply(message, translate, usage):
    chat_id = message.chat.id
    if message.text == translate:
        db = DB_Cards.DBCards(Settings.database, Settings.user, Settings.password, chat_id)
        correct_num = db.update_correct_attempts_num()
        markup = types.ReplyKeyboardMarkup(row_width=1)
        next_button = types.KeyboardButton(Command.NEXT)
        menu_button = types.KeyboardButton(Command.MENU)
        buttons = [next_button, menu_button]
        markup.add(*buttons)
        bot.send_message(message.chat.id, f'Верно!!! 💥\nВерно отгаданных слов: {correct_num}\n\n'
                                          f'Применение перевода:\n{usage}', reply_markup=markup)
        cards_logger.info(f'id{chat_id}: угадал слово.')
        bot.register_next_step_handler(message, show_cards)
    elif message.text == Command.ADD_WORD:
        add_word(message)
    elif message.text == Command.MISS:
        show_cards(message)
    elif message.text == Command.MENU:
        default_position(message)
    else:
        bot.send_message(chat_id, 'Ошибка, попробуйте ещё 😕')
        cards_logger.info(f'id{chat_id}: не угадал слово.')
        bot.register_next_step_handler(message, reply, translate, usage)


if __name__ == '__main__':
    print('Bot is running')
    bot.polling()

