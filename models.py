from dataclasses import dataclass, field, fields


@dataclass(slots=True)
class Car_data:
    # Общее
    url: str = field(default='')
    car_id: str = field(default='')  # id лота
    brand: str = field(default='')  # Марка автомобиля
    model: str = field(default='')  # Модель автомобиля
    model_2: str = field(default='')  # Модельный ряд
    mileage: int = field(default=0)  # Пробег автомобиля
    year: int = field(default=1900)  # Год выпуска
    location: str = field(default='')  # Местоположение
    title: str = field(default='')  # Наименование лота
    description: str = field(default='')  # Описание лота
    price_byn: int = field(default=0)  # Стоимость руб
    price_usd: int = field(default=0)  # Стоимость usd
    sellerName: str = field(default='')  # Имя продавца
    exchange: str = field(default='')  # Намерения продавца по обмену
    publishedAt: str = field(default='')  # Дата публикации
    refreshedAt: str = field(default='')  # Дата обновления
    photo: list = field(default_factory=list)  # Список ссылок на фотографии лота
    vin: str = field(default='')  # VIN номер автомобиля

    # Технические характеристики
    url_specifications: str = field(default='')

    # Габариты
    length: str = field(default='')  # Длина
    width: str = field(default='')  # Ширина
    height: str = field(default='')  # Высота

    # Кузов
    bodyType: str = field(default='')  # Тип кузова
    numberOfSeats: str = field(default='')  # Количество мест
    wheelbase: str = field(default='')  # Колесная база
    curbWeight: str = field(default='')  # Снаряженная масса
    groundClearance: str = field(default='')  # Дорожный просвет
    maxTrunkCapacity: str = field(default='')  # Объем багажника максимальный
    minTrunkCapacity: str = field(default='')  # Объем багажника минимальный
    fullWeight: str = field(default='')  # Полная масса
    frontTrackWidth: str = field(default='')  # Ширина передней колеи
    backTrackWidth: str = field(default='')  # Ширина задней колеи

    # Двигатель
    engineType: str = field(default='')  # Тип двигателя
    engineCapacity: str = field(default='')  # Объем
    enginePower: str = field(default='')  # Мощность
    maxPowerAtRpm: str = field(default='')  # Обороты максимальной мощности
    maximumTorque: str = field(default='')  # Максимальный крутящий момент
    turnoverOfMaximumTorque: str = field(default='')  # Обороты максимального крутящего момента
    injectionType: str = field(default='')  # Тип впуска
    cylinderLayout: str = field(default='')  # Расположение цилиндров
    numberOfCylinders: str = field(default='')  # Кол-во цилиндров
    valvesPerCylinder: str = field(default='')  # Кол-во клапанов на цилиндр
    compressionRatio: str = field(default='')  # Степень сжатия
    boostType: str = field(default='')  # Тип наддува
    cylinderBore: str = field(default='')  # Диаметр цилиндра
    strokeCycle: str = field(default='')  # Ход поршня
    enginePlacement: str = field(default='')  # Расположение двигателя
    maxPowerKW: str = field(default='')  # Максимальная мощность

    # Общая информация
    countryBrandItem: str = field(default='')  # Страна марки
    numberOfDoors: str = field(default='')  # Количество дверей
    carClass: str = field(default='')  # Класс автомобиля

    # Аккумуляторная батарея
    batteryCapacity: str = field(default='')  # Емкость батареи

    # Трансмиссия и управление
    gearBoxType: str = field(default='')  # Тип КПП
    numberOfGear: str = field(default='')  # Количество передач
    driveType: str = field(default='')  # Привод

    # Эксплуатационные показатели
    fuel: str = field(default='')  # Марка топлива
    maxSpeed: str = field(default='')  # Максимальная скорость
    acceleration0100KmH: str = field(default='')  # Разгон до 100 км/ч
    fuelTankCapacity: str = field(default='')  # Объем топливного бака
    emissionStandards: str = field(default='')  # Экологический стандарт
    cityDrivingFuelConsumptionPer100Km: str = field(default='')  # Расход топлива в городе на 100км
    highwayDrivingFuelConsumptionPer100Km: str = field(default='')  # Расход топлива на шоссе на 100км
    mixedDrivingFuelConsumptionPer100Km: str = field(default='')  # Расход топлива в смешанном цикле на 100км
    co2Emissions: str = field(default='')  # Выброс СО2

    # Подвеска и тормоза
    frontSuspension: str = field(default='')  # Передняя подвеска
    backSuspension: str = field(default='')  # Задняя подвеска
    frontBrakes: str = field(default='')  # Передние тормоза
    rearBrakes: str = field(default='')  # Задние тормоза

# print([el.name for el in fields(Car_data)])
