import math
from dataclasses import astuple
import requests
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from environs import Env
from transliterate import translit
from pprint import pprint
from models import *
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

    def retry_function(self, function, max_attempts, *args, **kwargs):
        """
        Функция повторного вызова функции max_attempts раз, если не успешно то взвращает None
        После вызова настоящей функции необходимо прописать обработку на случай результата None
        :param function: вызываемая функция
        :param max_attempts: количество раз вызова функции
        :return: результат вызываемой функции, в случае не успешного вызова None
        """
        attempt = 1
        while attempt <= max_attempts:
            try:
                result = function(*args, **kwargs)  # Вызов переданной функции
                return result
            except Exception as e:
                attempt += 1
                if attempt == max_attempts:
                    return None
                print(f'Ошибка {str(e)} попытка {attempt}')
        return None

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

    @classmethod
    def save_data(cls, data: list) -> None:
        data = [astuple(i) for i in data]
        cls.DB.update_query("""
        WITH car_id as(
            INSERT INTO website_cars(url, car_id, brand, model, model_2, mileage, year, location, title, description, 
                                     price_byn, price_usd, sellername, exchange, publishedat, refreshedat, vin, 
                                     url_specifications, length, width, height, bodytype, numberofseats, wheelbase, 
                                     curbweight, groundclearance, maxtrunkcapacity, mintrunkcapacity, fullweight, 
                                     fronttrackwidth, backtrackwidth, enginetype, enginecapacity, enginepower, 
                                     maxpoweratrpm, maximumtorque, turnoverofmaximumtorque, injectiontype, 
                                     cylinderlayout, numberofcylinders, valvespercylinder, compressionratio, boosttype, 
                                     cylinderbore, strokecycle, engineplacement, maxpowerkw, countrybranditem, 
                                     numberofdoors, carclass, batterycapacity, gearboxtype, numberofgear, drivetype, 
                                     fuel, maxspeed, acceleration0100kmh, fueltankcapacity, emissionstandards, 
                                     citydrivingfuelconsumptionper100km, highwaydrivingfuelconsumptionper100km, 
                                     mixeddrivingfuelconsumptionper100km, co2emissions, frontsuspension, backsuspension, 
                                     frontbrakes, rearbrakes)
            VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET price_byn = excluded.price_byn, price_usd = excluded.price_usd 
            RETURNING id)
            INSERT INTO website_photos(photo, car_id)
            VALUES (unnest(COALESCE(%s, ARRAY[]::text[])), (SELECT id FROM car_id))
            ON CONFLICT (photo) DO NOTHING
        """, data, many=True)

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
            print('ОШИБКА', name_json)
            print(data['props']['initialState']['landing']['seo']['links'])

        return list_models

    def get_brand_model_links(self, soup: BeautifulSoup, link: str) -> list:
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

    def __get_data(self, link: str) -> Car_data:
        # print('\n', link)
        data = ''
        at = 1
        while at <= 3:
            try:
                data = self.get_json(self.get_soup(link))
                break
            except Exception as e:
                print(str(e))
                at += 1

        car = Car_data(link)

        # Общее
        car.car_id = data['props']['initialState']['advert']['advert']['id']  # id лота
        car.brand = [el['value'] for el in data['props']['initialState']['advert']['advert']['properties'] if
                     el['name'] == 'brand'][0]  # Марка автомобиля
        car.model = [el['value'] for el in data['props']['initialState']['advert']['advert']['properties'] if
                     el['name'] == 'model'][0]  # Модель автомобиля
        try:
            car.model_2 = [el['value'] for el in data['props']['initialState']['advert']['advert']['properties'] if
                           el['name'] == 'generation'][0]  # Модельный ряд
        except Exception:
            car.model_2 = ''
        try:
            car.mileage = [el['value'] for el in data['props']['initialState']['advert']['advert']['properties'] if
                           el['name'] == 'mileage_km'][0]  # Пробег автомобиля
        except Exception:
            car.mileage = -1
        try:
            car.year = data['props']['initialState']['advert']['advert']['year']  # Год выпуска
        except Exception:
            car.year = -1
        try:
            car.location = data['props']['initialState']['advert']['advert']['locationName']  # Местоположение
        except Exception:
            car.location = ''
        try:
            car.title = data['props']['initialState']['landing']['seo']['metaInfo']['h1']  # Наименование лота
        except Exception:
            car.title = ''
        try:
            car.description = data['props']['initialState']['landing']['seo']['metaInfo'][
                'ogDescription']  # Описание лота
        except Exception:
            car.description = ''
        car.price_byn = data['props']['initialState']['advert']['advert']['price']['byn']['amount']  # Стоимость руб
        try:
            car.price_usd = data['props']['initialState']['advert']['advert']['price']['usd']['amount']  # Стоимость usd
        except Exception:
            car.price_usd = 0
        try:
            car.sellername = data['props']['initialState']['advert']['advert']['sellerName']  # Имя продавца
        except Exception:
            car.sellername = ''
        car.exchange = data['props']['initialState']['advert']['advert']['exchange'][
            'label']  # Намерия продавца по обмену
        car.publishedAt = data['props']['initialState']['advert']['advert']['publishedAt']  # Дата публикации
        car.refreshedAt = data['props']['initialState']['advert']['advert']['refreshedAt']  # Дата обновления
        try:
            car.vin = data['props']['initialState']['advert']['advert']['metadata']['vinInfo'][
                'vin']  # VIN номер автомобиля
        except Exception:
            car.vin = ''
        car.photo = [el['medium']['url'] for el in
                     data['props']['initialState']['advert']['advert']['photos']]  # Список ссылок на фотографии лота

        # Технические характеристики
        try:
            car.url_specifications = data['props']['initialState']['catalog']['advertModifications'][
                'url']  # Ссылка на технические характеристики
            print(car.url_specifications)
            soup_specifications = self.get_soup(car.url_specifications)
            json_data_specifications = soup_specifications.find('script', id='__NEXT_DATA__').text
            data_specifications = json.loads(json_data_specifications)

            # Габариты
            try:
                car.length = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'length']  # Длина
            except Exception:
                car.length = ''
            try:
                car.width = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'width']  # Ширина
            except Exception:
                car.width = ''
            try:
                car.height = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'height']  # Высота
            except Exception:
                car.height = ''

            # Кузов
            try:
                car.bodyType = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'bodyType']  # Тип кузова
            except Exception:
                car.bodyType = ''
            try:
                car.numberOfSeats = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'numberOfSeats']  # Количество мест
            except Exception:
                car.numberOfSeats = ''
            try:
                car.wheelbase = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'wheelbase']  # Колесная база
            except Exception:
                car.wheelbase = ''
            try:
                car.curbWeight = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'curbWeight']  # Снаряженная масса
            except Exception:
                car.curbWeight = ''
            try:
                car.groundClearance = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'groundClearance']  # Дорожный просвет
            except Exception:
                car.groundClearance = ''
            try:
                car.maxTrunkCapacity = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'maxTrunkCapacity']  # Объем багажника максимальный
            except Exception:
                car.maxTrunkCapacity = ''
            try:
                car.minTrunkCapacity = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'minTrunkCapacity']  # Объем багажника минимальный
            except Exception:
                car.minTrunkCapacity = ''
            try:
                car.fullWeight = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'fullWeight']  # Полная масса
            except Exception:
                car.fullWeight = ''
            try:
                car.frontTrackWidth = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'frontTrackWidth']  # Ширина передней колеи
            except Exception:
                car.frontTrackWidth = ''
            try:
                car.backTrackWidth = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'backTrackWidth']  # Ширина задней колеи
            except Exception:
                car.backTrackWidth = ''

            # Двигатель
            try:
                car.engineType = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'engineType']  # Тип двигателя
            except Exception:
                car.engineType = ''
            try:
                car.engineCapacity = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'engineCapacity']  # Объем
            except Exception:
                car.engineCapacity = ''
            try:
                car.enginePower = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'enginePower']  # Мощность
            except Exception:
                car.enginePower = ''
            try:
                car.maxPowerAtRpm = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'maxPowerAtRpm']  # Обороты максимальной мощности
            except Exception:
                car.maxPowerAtRpm = ''
            try:
                car.maximumTorque = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'maximumTorque']  # Максимальный крутящий момент
            except Exception:
                car.maximumTorque = ''
            try:
                car.turnoverOfMaximumTorque = \
                    data_specifications['props']['initialState']['catalog']['modificationCard'][
                        'turnoverOfMaximumTorque']  # Обороты максимального крутящего момента
            except Exception:
                car.turnoverOfMaximumTorque = ''
            try:
                car.injectionType = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'injectionType']  # Тип впуска
            except Exception:
                car.injectionType = ''
            try:
                car.cylinderLayout = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'cylinderLayout']  # Расположение цилиндров
            except Exception:
                car.cylinderLayout = ''
            try:
                car.numberOfCylinders = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'numberOfCylinders']  # Кол-во цилиндров
            except Exception:
                car.numberOfCylinders = ''
            try:
                car.valvesPerCylinder = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'valvesPerCylinder']  # Кол-во клапанов на цилиндр
            except Exception:
                car.valvesPerCylinder = ''
            try:
                car.compressionRatio = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'compressionRatio']  # Степень сжатия
            except Exception:
                car.compressionRatio = ''
            try:
                car.boostType = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'boostType']  # Тип наддува
            except Exception:
                car.boostType = ''
            try:
                car.cylinderBore = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'cylinderBore']  # Диаметр цилиндра
            except Exception:
                car.cylinderBore = ''
            try:
                car.strokeCycle = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'strokeCycle']  # Ход поршня
            except Exception:
                car.strokeCycle = ''
            try:
                car.enginePlacement = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'enginePlacement']  # Расположение двигателя
            except Exception:
                car.enginePlacement = ''
            try:
                car.maxPowerKW = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'maxPowerKW']  # Максимальная мощность
            except Exception:
                car.maxPowerKW = ''

            # Общая информация
            try:
                car.countryBrandItem = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'countryBrandItem']  # Страна марки
            except Exception:
                car.countryBrandItem = ''
            try:
                car.numberOfDoors = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'numberOfDoors']  # Количество дверей
            except Exception:
                car.numberOfDoors = ''
            try:
                car.carClass = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'carClass']  # Класс автомобиля
            except Exception:
                car.carClass = ''

            # Аккумуляторная батарея
            try:
                car.batteryCapacity = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'batteryCapacity']  # Емкость батареи
            except Exception:
                car.batteryCapacity = ''

            # Трансмиссия и управление
            try:
                car.gearBoxType = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'gearBoxType']  # Тип КПП
            except Exception:
                car.gearBoxType = ''
            try:
                car.numberOfGear = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'numberOfGear']  # Количество передач
            except Exception:
                car.numberOfGear = ''
            try:
                car.driveType = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'driveType']  # Привод
            except Exception:
                car.driveType = ''

            # Эксплуатационные показатели
            try:
                car.fuel = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'fuel']  # Марка топлива
            except Exception:
                car.fuel = ''
            try:
                car.maxSpeed = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'maxSpeed']  # Максимальная скорость
            except Exception:
                car.maxSpeed = ''
            try:
                car.acceleration0100KmH = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'acceleration0100KmH']  # Разгон до 100 км/ч
            except Exception:
                car.acceleration0100KmH = ''
            try:
                car.fuelTankCapacity = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'fuelTankCapacity']  # Объем топливного бака
            except Exception:
                car.fuelTankCapacity = ''
            try:
                car.emissionStandards = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'emissionStandards']  # Экологический стандарт
            except Exception:
                car.emissionStandards = ''
            try:
                car.cityDrivingFuelConsumptionPer100Km = \
                    data_specifications['props']['initialState']['catalog']['modificationCard'][
                        'cityDrivingFuelConsumptionPer100Km']  # Расход топлива в городе на 100км
            except Exception:
                car.cityDrivingFuelConsumptionPer100Km = ''
            try:
                car.highwayDrivingFuelConsumptionPer100Km = \
                    data_specifications['props']['initialState']['catalog']['modificationCard'][
                        'highwayDrivingFuelConsumptionPer100Km']  # Расход топлива на шоссе на 100км
            except Exception:
                car.highwayDrivingFuelConsumptionPer100Km = ''
            try:
                car.mixedDrivingFuelConsumptionPer100Km = \
                    data_specifications['props']['initialState']['catalog']['modificationCard'][
                        'mixedDrivingFuelConsumptionPer100Km']  # Расход топлива в смешанном цикле на 100км
            except Exception:
                car.mixedDrivingFuelConsumptionPer100Km = ''
            try:
                car.co2Emissions = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'co2Emissions']  # Выброс СО2
            except Exception:
                car.co2Emissions = ''

            # Подвеска и тормоза
            try:
                car.frontSuspension = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'frontSuspension']  # Передняя подвеска
            except Exception:
                car.frontSuspension = ''
            try:
                car.backSuspension = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'backSuspension']  # Задняя подвеска
            except Exception:
                car.backSuspension = ''
            try:
                car.frontBrakes = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'frontBrakes']  # Передние тормоза
            except Exception:
                car.frontBrakes = ''
            try:
                car.rearBrakes = data_specifications['props']['initialState']['catalog']['modificationCard'][
                    'rearBrakes']  # Задние тормоза
            except Exception:
                car.rearBrakes = ''
        except Exception:
            car.url_specifications = 'None_spec'

        return car

    def runner(self, start_url: str):
        """
        Функция получения данных по всем объявлениям
        :param start_url: Стартовая страница сайта
        :return: В результате ее выполнения полученные данные выгружаются в БД.
        """
        link_template = f'https://cars.av.by/'
        # Получаем список всех марок автомобилей
        list_brands = self.get_brands(self.get_soup(start_url))

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
            # model_links_list = []
            for model in tqdm(list_models, desc='Загрузка ссылок Брэнда:', colour='green'):
                print('\n', f'Марка {brand} модель {model}')

                # Делаем транслитерацию русских названий брэндов
                md = translit(model.strip().replace('(', '').replace(')', '').replace(' ', '-').lower(), 'ru',
                              reversed=True)
                # Формируем ссылку страницы данной модели
                link_model = f'{link_brand}/{md}'
                # Получаем список всех ссылок объявлений по текущему брэнду
                soup_model = self.get_soup(link_model)
                model_links_list = self.retry_function(self.get_brand_model_links, 3, soup_model, link_model)
                if model_links_list == None:
                    continue

                # Собираем данные по автомобилям текущей модели
                car_data = []
                try:
                    for link in model_links_list:
                        print('\n', link)
                        data = self.retry_function(self.__get_data, 3, link)
                        if not data == None:
                            car_data.append(data)
                        else:
                            continue
                    # Выгружаем полученные данные в БД
                    # pprint(car_data)
                    self.save_data(car_data)
                except Exception:
                    continue


car = Parser_car()
car.runner('https://av.by/')
