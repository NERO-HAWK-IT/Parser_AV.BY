import psycopg2  # библиотека необходимая для работы с PostgreSQL
from psycopg2 import extras
from environs import Env  # для тестирования DB_client

env = Env()
env.read_env()  # Чтение аргументов подключения к БД

db_name = env('DBNAME')
db_user = env('DBUSER')
db_password = env('DBPASSWORD')
db_host = env('HOST')
db_port = env('PORT')


class DB_Postgres:
    # Реализуем патерн синглтон, чтобы не плодить подключения
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Переопределение функции класса __new__ - патерн синглотон, необходимый для того чтобы не плодить подключения
        :param args: -
        :param kwargs: -
        """
        if cls.__instance is None:  # Проверяем выделена ли память под заданный объект
            cls.__instance = super().__new__(cls)  # Присваиваем адрес в памяти для объектов класса
        return cls.__instance

    def __init__(self, dbname, user, password, host, port):
        """
        Функция ининциализации переменных необходимых для подключения к БД.
        :param db_name: наименование БД
        :param user: имя пользователь (для входа в БД)
        :param password: Пароль (ля входа в ДБ)
        :param host: наименование хоста к которому будем подключаться
        :param port: адрес порта на который будем подключаться
        """
        self.__dbname = dbname
        self.__user = user
        self.__password = password
        self.__host = host
        self.__port = port

    def fetch_one(self, query: str, data: tuple = None, factory=None, clean=None):
        """
        Функция для вывода данных одной записи
        :param query: запрос
        :param data: данные
        :param factory: тип в котором передаются данные
        :param clean: ????
        :return: возвращает данные первой запись БД, с каждым последующим вызовом данные последующей записи
        """
        try:
            with self.__connect(factory) as cursor:
                self.__execute(cursor, query, data)
                return self.__fetch(cursor, clean)
        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def fetch_all(self, query: str, data: tuple = None, factory=None):
        """
        Функция для вывода данных всех записей
        :param query: запрос
        :param data: данные
        :param factory: тип в котором передаются данные
        :return: возвращает данные всех записей
        """
        try:
            with self.__connect(factory) as cursor:
                self.__execute(cursor, query, data)
                return cursor.fetchall()
        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def update_query(self, query: str,  data: [tuple | list] = None, many=False, message='OK'):
        """
        Функция для обновления данных в БД.
        :param query: запрос
        :param data: данные
        :param many: тригер указывающий сколько записей мы будем загружать в БД True - много, False - одну
        :param message: Сообщение о результате выполнения запроса, по умолчанию "ОК"
        :return:
        """
        try:
            with self.__connect() as cursor:
                self.__execute(cursor, query, data, many)
                print(message)  # Сообщение выводится при удачном выполнении запроса
        except (Exception, psycopg2.Error) as error:
            self.__error(error)

    def __connect(self, factory: str = None):
        """
        Функция для подключения к БД
        :param factory: в каком виде функция примает параметры:
        1. словарь; 2. список 3. кортеж - соответственно в аналогичном формате будет выводиться курсор
        :return: возвращает курсор (cursor)
        """
        # Передаем необходимые параметры для подключения к БД
        connection = psycopg2.connect(
            dbname=self.__dbname,
            user=self.__user,
            password=self.__password,
            host=self.__host,
            port=self.__port
        )
        connection.autocommit = True  # комит всех сохранений
        # определяем курсор в зависимости от того в каком виде нам приходят данные
        # (курсор делает запросы и получает их результаты)
        if factory == 'dict':
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        elif factory == 'list':
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cursor = connection.cursor()

        return cursor

    @staticmethod
    def __execute(cursor, query, data=None, many=False):
        """
        Функция для записи данных в БД
        :param cursor: курсор
        :param query: запрос
        :param argument: аргументы
        :param many: тригер указывающий сколько записей мы будем загружать в БД True - много, False - одну
        :return:
        """
        if many:
            if data:
                cursor.executemany(query, data)
            else:
                cursor.execute(query)
        else:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)

    @staticmethod
    def __fetch(cursor, clean):  # Ивану, нужно более подробно уточнить, для чего это и для чего clean
        """
        Функция для получения  данных из БД.
        :param cursor: курсор
        :param clean: тригер позволяющий вернуть
        :return:
        """
        if clean is None:
            fetch = cursor.fetchone()
        else:
            fetch = cursor.fetchone()[0]

        return fetch

    @staticmethod
    def __error(error):
        """
        Функция для вывода ошибок
        :param error: принимает системную ошибку
        :return: взвращает описание ошибки
        """
        print(error)

# db = DB_Postgres(db_name, db_user, db_password, db_host, db_port)
