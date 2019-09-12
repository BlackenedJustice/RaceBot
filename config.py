from peewee import *
import os
import urllib.parse as urlparse

token = '874988148:AAFf1SgspG6636CNp6ZNV4VyHEHPbqoNi1U'
creatorID = 144454876
creatorUsername = 'yury_zh'


if 'HEROKU' in os.environ:
    DEBUG = False
    urlparse.uses_netloc.append('postgres')
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    DATABASE = {
        'engine': 'peewee.PostgresqlDatabase',
        'name': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port,
    }
else:
    DEBUG = True
    DATABASE = {
        'engine': 'peewee.PostgresqlDatabase',
        'name': 'yury',
        'user': 'yury',
        'password': '508087yhpR',
        'host': 'localhost',
        'port': 5432,
        'threadlocals': True
    }

db = PostgresqlDatabase(
    DATABASE.get('name'),
    user=DATABASE.get('user'),
    password=DATABASE.get('password'),
    host=DATABASE.get('host'),
    port=DATABASE.get('port')
)

# db = SqliteDatabase('data.db')

warningWrongDataFormat = 'Проверьте, что вы ввели текст и попробуйте ещё раз'
userRegistered = 'Вы уже зарегистрированы!'
greetings = 'Вы успешно зарегистрированы!\nВведите команду /help посмотреть список доступных команд'
getName = 'Введите ваше имя'
wrongName = 'Имя должно быть текстом! Введите команду /set_name еще раз'
doesNotExist = 'Вы не зарегистрированы! Введите команду /start чтобы начать'

group_numbers = [101 + i for i in range(19)] + [141]

commands = [
    '/info - текущий рейтинг\n/show <group> - показать очки конкретной группы\n/help - показать это сообщение',
    '/info - текущий рейтинг\n/show <group> - показать очки конкретной группы\n'
    '/add <group_no> <points> - добавить очки группе\n'
    '/del <group_no> <points> - снять очки с группы\n/wall <msg> - отправить сообщение организаторам'
    '/everyone <msg> - отправить сообщение всем пользователям\n/set_name - установить себе имя'
    '\n/help - показать это сообщение',
    '/info - текущий рейтинг\n/show <group> - показать очки конкретной группы\n'
    '/add <group_no> <points> - добавить очки группе\n'
    '/del <group_no> <points> - снять очки с группы\n/reset - обнулить все очки\n'
    '/wall <msg> - отправить сообщение организаторам'
    '/everyone <msg> - отправить сообщение всем пользователям\n/set_name - установить себе имя'
    '\n/help - показать это сообщение',
]
