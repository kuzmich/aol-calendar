import enum


PUBLIC_LINK_TEMPLATE = 'https://artofliving.ru/{event_path}?streamId={event_id}#offerBlock'


COURSE_NAME_TYPE = {
    'art excel': 'art_excel',
    'dsn': 'dsn',
    'дсн': 'dsn',
    'vtp online': 'vtp_online',
    'yes!': 'yes',
    'yes+': 'yes_plus',
    'блессинг': 'blessing',
    'глубокий сон и снятие тревожности': 'deep_sleep',
    # 'забота о спине и коррекция осанки': 'spine_care',
    'забота о позвоночнике и осанке': 'healthy_posture',
    'здоровое питание': 'cooking',
    'искусство жизни — премиум': 'premium',
    'искусство медитации': 'meditation',
    'искусство тишины': 'silence',
    'искусство тишины online': 'silence_online',
    # 'искусство тишины интенсив': 'silence_intense',
    'йога': 'yoga',
    'йога для позвоночника': 'yoga_spine',
    'первый шаг': 'first_step',
    'песенный сатсанг': 'satsang',  # 🎸
    'победи зависимость': 'give_up_smoking',
    'поддерживающее занятие': 'practices',
    'поддерживающее занятие online': 'practices_online',
    'поддерживающее занятие для vtp': 'practices_vtp',
    'процесс вечности': 'eternity',
    'процесс интуиции': 'intuition',
    'процесс интуиции 5-8 лет': 'intuition_5_8',
    'процесс интуиции 8-18 лет': 'intuition_8_18',
    'саньям': 'sanyam',
    'саньям 2': 'sanyam2',
    'суставная йога': 'yoga_joints',
    'счастье': 'happiness',
    'счастье онлайн': 'happiness_online',
    # 'счастье (благотворительный)': 'happiness',
    'шри шри йога': 'ssy',
    'шри шри йога 2': 'ssy2',
}


# PATH - это path публичной ссылки на сайте
# TYPE - это тип курса из COURSE_NAME_TYPE
EVENT_TYPE_PATH = {
    'art_excel': "artexcel",
    'blessing': "blessing",
    'cooking': "cookie",
    'deep_sleep': "deep-sleep",
    'dsn': "dsn",
    'eternity': 'process_vechnosti',
    'first_step': "firststep",
    'give_up_smoking': "give-up-smoking",
    'happiness': "happiness",
    'healthy_posture': 'healthy-posture',
    'intuition': "intuition-process-8-18",
    'intuition_5_8': "intuition-process-5-7",
    'intuition_8_18': "intuition-process-8-18",
    'meditation': "meditation",
    'practices_online': "practice-online",
    'premium': "premium",
    'sanyam': 'sanyam',
    'sanyam2': 'sanyam2',
    'silence': "art-of-silence",
    'silence_online': "art-of-silence_online",
    'ssy': "yoga",
    'ssy2': "srisriyoga2",
    'vtp_online': "vtp_online",
    'yes': "yes",
    'yes_plus': "yesplus",
}


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
