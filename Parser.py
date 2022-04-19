import datetime
import csv
import bs4
import requests

BASE_URL = "https://www.culture.ru/afisha/"

TAGS = {
    "для молодежи": 'tags-dlya-molodezhi',
    'культура онлайн': 'tags-kultura-onlain',
    'день театра': 'tags-den-teatra',
    'для детей': 'tags-dlya-detei',
    'бесплатно': 'tags-besplatno'
}

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/89.0.4389.128 Safari/537.36',
    'Accept-Language': 'ru',
}

TIME_FORMAT_STRING = '%Y-%M-%d'

FIELD_NAMES = ['event_name', 'date', 'place', 'price', 'ref']

SOUP_PARSER = 'html.parser'


class Parser:
    def __init__(self, headers=None):
        if headers is None:
            headers = DEFAULT_HEADERS

        self.__url = BASE_URL
        self.__session = requests.Session()
        self.__session.headers = headers
        self.__page_limit = 1

    @staticmethod
    def __parse_block(block) -> dict:
        """
        Преобразует содержимое блока в словарь
        :param block: блок события
        :return: словарь с содержимим события
        """

        def none_str_handler(v):
            return '' if v is None else v.text

        def none_ref_handler(v):
            return '' if v is None else v.get('href')

        dct = {'event_name': none_str_handler(block.find("div", class_="fRPti")),
               'date': none_str_handler(block.find("div", class_="r8tBP")),
               'place': none_str_handler(block.find("div", class_="_1gZxm")),
               'price': none_str_handler(block.find("div", class_="ijT3l")),
               'ref': BASE_URL + none_ref_handler(block.find("a", class_="G8w3d"))}
        return dct

    def __get_page(self, page: int = 0) -> str:
        """
        Возвращает страницу по заданному номеру
        :param page: номер запрашиваемой страници
        :return: содержимое страницы
        """
        params = {'page': page}
        r = self.__session.get(self.__url, params=params)
        return r.text

    def __get_event_data(self, page: int = None) -> list:
        """
        Возвращает блок события
        :param page: номер запрашиваемой страници
        :return: содержимое блока
        """
        text = self.__get_page(page=page)
        soup = bs4.BeautifulSoup(text, SOUP_PARSER)
        content_blocks = soup.find_all("div", class_="CHPy6")
        return [self.__parse_block(block) for block in content_blocks]

    def __get_page_limit(self) -> int:
        """
        Определят номер максимальной страницы
        :return: номер страицы
        """
        soup = bs4.BeautifulSoup(self.__get_page(page=1), SOUP_PARSER)
        page_buttons = soup.find_all("a", class_="_9LAqO")
        return max([int(button.text) for button in page_buttons])

    def __define_url(self,
                     region: str = None,
                     tag: str = None,
                     start: str = None,
                     end: str = None) -> str:
        """
        Определят URL для запросов на основе параметров
        :param region: регион
        :param tag: тег
        :param start: дата начала
        :param end: дата конца
        :return: конечный url
        """

        def format_time_validator(t):
            try:
                datetime.datetime.strptime(t, TIME_FORMAT_STRING)
                return t
            except ValueError as e:
                print(f"Некорректное значение. Дата должна удовлетворять формату: {TIME_FORMAT_STRING}", e)
                return ''

        region = 'russia/' if region is None else region
        tag = '' if tag is None else tag
        start = '' if start is None \
            else ('seanceStartDate-' +
                  format_time_validator(start)
                  + '/')
        end = '' if end is None else ('seanceEndDate-' + format_time_validator(end) + '/')
        tag = '' if str.lower(tag) not in TAGS.keys() else (TAGS[str.lower(tag)] + '/')

        url = BASE_URL + region + tag + start + end
        return url

    def parse(self,
              filename: str = None,
              region: str = None,
              tag: str = None,
              start: str = None,
              end: str = None,
              page_limit: int = None) -> None:
        """
        Парсит данные с сайта на основе параметров. Сохраняет данные в csv файл
        :param filename: имя итогового файла
        :param region: регион
        :param tag: тег
        :param start: дата начала
        :param end: дата конца
        :param page_limit: лимит страниц для поиска
        """

        self.__url = self.__define_url(region, tag, start, end)
        self.__page_limit = int(self.__get_page_limit() if (page_limit is None) else page_limit)

        with open(filename, 'w', encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES)
            writer.writeheader()

            for page in range(1, self.__page_limit + 1):
                writer.writerows(self.__get_event_data(page))
                print(f'Обработано {page} из {self.__page_limit}')
