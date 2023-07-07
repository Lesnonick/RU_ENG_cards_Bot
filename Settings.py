class Settings:
    API_TOKEN = ''
    DICT_TOKEN = ''
    database = ''
    user = ''
    password = ''


class Command:
    ADD_WORD = '➕ Добавить слово'
    DELETE_WORD = '🗑️ Удалить слово'
    MISS = '🤷‍ Пропустить'
    LIST = '/list'
    HELP = '/help'
    CARDS = '/cards'
    CLEAN = '/clean'
    MENU = '🖥️ К меню бота'
    NEXT = '➡ Следующее слово'
    YES = '✅ Да'
    CHANGE_ALL = '💫 Поменять всё'
    CHANGE_USAGE = '🔄 Поменять пример использования'
    CANCEL = '❌ Отменить добавление'


class Replies:
    WORD_ADDED = 'Слово успешно добавлено ✅'
    ADD_CANCELED = 'Добавление отменено ❌'
    NUM_WORD = 'Слов изучается:'