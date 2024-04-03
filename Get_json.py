import json

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, TypeAdapter, field_validator

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

# URL страницы раздела сайта с которого парсим данные
URL = 'https://cars.av.by/avart'

def get_html_page(key_page: str, name_json: str):
    """
    Функция выгрузки HTML кода страницы.
    URL_page : одинаковая часть URL страниц (при пагинации)
    :param key_page: уникальный ключ страницы (при пагинации)
    :param name_json: название Json файла
    :return: сохраняет в каталог JSON HTML код
    """
    response = requests.get(f'{URL}{key_page}', headers=HEADERS)
    print(response.status_code, 'JSON Загружен')
    response = response.text
    soup = BeautifulSoup(response, 'lxml').find('script', id='__NEXT_DATA__').text
    data = json.loads(soup) #['props']['initialState']['catalog']['landing']['title']
    with open(f'{name_json}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))  # Преобразуем полученный код в читабельный вид


get_html_page('', 'cars')

