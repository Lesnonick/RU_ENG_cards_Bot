from Settings import Settings
import requests
from Cards_logger import cards_logger


class YandexDict:

    base_host = 'https://dictionary.yandex.net/'

    def __init__(self, token):
        self.token = token

    def get_translate(self, rus_word):
        url = 'api/v1/dicservice.json/lookup'
        request_url = self.base_host + url
        params = {'key': self.token, 'lang': 'ru-en', 'text': rus_word}
        try:
            response = requests.get(request_url, params=params)
        except requests.exceptions.RequestException:
            cards_logger.error(f'Ошибка в Яндекс.Словарь API: {requests.exceptions.RequestException}')
            return 'No connection to dictionary', None
        try:
            translate = response.json()['def'][0]['tr'][0]['text']
            part_of_speach = response.json()['def'][0]['tr'][0]['pos']
            return translate, part_of_speach
        except LookupError:
            cards_logger.warning(f'Ошибка в Яндекс.Словарь API: Перевод слова {rus_word} отсутствует.')
            return 'No translation in dictionary', None


class DictOnline:
    def get_example(self, eng_word, pos):
        url = 'https://api.dictionaryapi.dev/api/v2/entries/en/'
        request_url = url + eng_word
        example = 'Sorry, no application found.'
        try:
            response = requests.get(request_url)
        except requests.exceptions.RequestException:
            cards_logger.error(f'Ошибка в Dict Online API: {requests.exceptions.RequestException}')
            return example
        try:
            meanings = response.json()[0]['meanings']
        except LookupError:
            return example
        for meaning in meanings:
            if meaning['partOfSpeech'] == pos:
                try:
                    example = meaning['definitions'][0]['example']
                except LookupError:
                    cards_logger.warning(f'Ошибка в Dict Online API: Применение слова {eng_word} отсутствует.')
                    return example
        return example


def get_translate_and_example(rus_word):
    yad = YandexDict(Settings.DICT_TOKEN)
    dicton = DictOnline()
    translate, pos = yad.get_translate(rus_word)
    if pos is not None:
        example = dicton.get_example(translate, pos)
    else:
        example = 'No application for unknown word'
    return translate, example

