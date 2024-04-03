import re
import math
from dataclasses import astuple
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from environs import Env
from transliterate import translit
from pprint import pprint

from models import Car_data
from DB_client import DB_Postgres

env = Env()
env.read_env()
db_name = env('DBNAME')
db_user = env('DBUSER')
db_password = env('DBPASSWORD')
db_host = env('HOST')
db_port = env('PORT')


class Parser_car:
    # Данные для автооризации на сайте
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }

    DB = DB_Postgres(db_name, db_user, db_password, db_host, db_port)

    @classmethod
    def get_soup(cls, url: str) -> BeautifulSoup:
        """
        Функция подключения и получения кода страницы.
        :param url: URL страницы к которой подключаемся
        :return: возвращает данные страницы
        """
        response = requests.get(url, headers=cls.HEADERS)
        # print(f'{response.status_code} | {url}')
        soup = BeautifulSoup(response.text, 'lxml')

        return soup

    def get_json(self, soup: BeautifulSoup):
        """
        Функция поучения NEXT_DATA в формате json
        :param soup: СУП страницы
        :return: NEXT DATA в формате json
        """
        json_data = soup.find('script', id='__NEXT_DATA__').text
        data = json.loads(json_data)

        return data

    def get_brands(self, soup: BeautifulSoup) -> list:
        """
        Функция для получения всех доступных марок авто
        :param soup: СУП стартовой страницы
        :return: список доступных марок
        """
        data = self.get_json(soup)
        list_drands = []
        for el in data['props']['initialState']['home']['links']:
            list_drands.append(el['label'])
        return list_drands

    def get_brand_models(self, soup: BeautifulSoup) -> list:
        """
        Функция для получения всех доступных моделей марки авто
        :param soup: Суп страницы марки авто
        :return: список доступных моделей
        """
        data = self.get_json(soup)
        list_models = []
        try:
            for el in data['props']['initialState']['landing']['seo']['links']:
                list_models.append(el['label'])
        except Exception:
            name_json = data['props']['initialState']['app']['entryUrl']
            print(name_json)
            print(data['props']['initialState']['landing']['seo']['links'])

        return list_models

    def get_brand_model_links(self, soup: BeautifulSoup, link: str):
        """
        Функция для получения ссылок страниц с объявлениями по одной модели брэнда
        :param soup: СУП страницы модели брэнда
        :param link: ссылка стартовой страницы модели брэнда
        :return: список ссылок страниц с объявлениями по модели брэнда
        """
        links = []

        # Получаем количество страниц с объявлениями по данной модели
        try:
            items = soup.find('button', class_="button button--secondary button--block").find('span').text
            page_count = math.ceil(int(items.replace(' ', '').split()[1]) / 25)
        except Exception:
            page_count = 1
        print('\n', f'Количество страниц с моделями {page_count}')
        url_next = link
        for el in tqdm(range(1, page_count + 1), desc='Загрузка ссылок '):
            if el != 1:
                # Получаем параметры для последующих ссылок страниц с объявлениями
                soup_next_link = self.get_soup(url_next)
                computing_1 = soup_next_link.find('div', {'class': 'paging__button'}).find('a').get('href')
                computing_2 = computing_1[computing_1.find('=') + 1:]
                param_brand = computing_2[:computing_2.find('&')]
                computing_3 = computing_2[computing_2.find('=') + 1:]
                param_model = computing_3[:computing_3.find('&')]
                url_next = f'https://cars.av.by/filter?brands[0][brand]={param_brand}&brands[0][model]={param_model}&page={el}'
            # Получаем ссылки всех страниц объявлений
            soup_link = self.get_soup(url_next)
            data = self.get_json(soup_link)
            try:
                car_links = list(data['props']['initialState']['filter']['main']['adverts'])
            except Exception:
                break
            for car_link in car_links:
                links.append(car_link['publicUrl'])

        return links

    def get_cars_link(self, start_url: str) -> list:
        """
        Функция сбора ссылок страниц всех объявлений
        :param start_url: Стартовая страница сайта
        :return: список ссылок всех страниц объявлений
        """
        link_list = []
        link_template = f'https://cars.av.by/'
        # Получаем список всех марок автомобилей
        list_brands = self.get_brands(self.get_soup(start_url))
        # list_brands= ['ford']
        for brand in tqdm(list_brands, desc='Загрузка Моделей брэнда:', colour='blue'):

            # Делаем транслитерацию русских названий брэндов
            br = translit(brand.strip().replace('(', '').replace(')', '').replace(' ', '-').lower(), 'ru',
                          reversed=True)
            # На сайте найдены некоторые косячные брэнды, исправляем это
            if br == 'avatr':
                br = 'avart'
            elif br == 'dongfeng':
                br = 'dong-feng'

            # Формируем ссылку по брэнду
            link_brand = f'{link_template}{br}'

            # Получаем список моделей текущего брэнда
            list_models = self.get_brand_models(self.get_soup(link_brand))
            print('\n', f'Количество моделей брэнда {len(list_models)}')
            for model in tqdm(list_models, desc='Загрузка ссылок Брэнда:', colour='green'):
                print('\n',f'Марка {brand} модель {model}')

                # Делаем транслитерацию русских названий брэндов
                md = translit(model.strip().replace('(', '').replace(')', '').replace(' ', '-').lower(), 'ru',
                              reversed=True)
                # Формируем ссылку страницы данной модели
                link_model = f'{link_brand}/{md}'
                # Получаем список всех ссылок объявлений по текущему брэнду
                soup_model = self.get_soup(link_model)
                list_items = self.get_brand_model_links(soup_model, link_model)
                link_list.extend(list_items)

        return link_list

    def runner(self, start_url):
        link_list = self.get_cars_link(start_url)
        print(len(link_list))
        print(link_list)


car = Parser_car()
car.runner('https://av.by/')
