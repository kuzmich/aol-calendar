import enum


class WeekDay(enum.IntEnum):
    пн = 1
    вт = 2
    ср = 3
    чт = 4
    пт = 5
    сб = 6
    вс = 7

    mon = 1
    tue = 2
    wed = 3
    thu = 4
    fri = 5
    sat = 6
    sun = 7

    @classmethod
    def choices(cls):
        return [(wd.value, wd.name) for wd in cls]


class Month(enum.Enum):
    января = 1
    февраля = 2
    марта = 3
    апреля = 4
    мая = 5
    июня = 6
    июля = 7
    августа = 8
    сентября = 9
    октября = 10
    ноября = 11
    декабря = 12


class MonthName(enum.Enum):
    январь = 1
    февраль = 2
    март = 3
    апрель = 4
    май = 5
    июнь = 6
    июль = 7
    август = 8
    сентябрь = 9
    октябрь = 10
    ноябрь = 11
    декабрь = 12
