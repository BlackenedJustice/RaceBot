# coding=utf-8
from telebot import types
from telebot import apihelper
from peewee import DoesNotExist
from functools import wraps
import logging

import telebot
import config
from mwt import MWT
from config import db
from users import User, Groups, Role


logger = logging.getLogger('bot')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(token=config.token)
'''
# using proxy in Russia
apihelper.proxy = {
    # 'http': 'http://46.101.149.132:3128',
    # 'https': 'https://46.101.149.132:3128'
    # 'http': 'http://79.138.99.254:8080',
    # 'https': 'https://79.138.99.254:8080'
     'http': 'http://5.148.128.44:80',
     'https': 'https://5.148.128.44:80'
    # 'http': 'http://167.99.242.198:8080',
    # 'https': 'https://167.99.242.198:8080'
}
'''
# create tables in db
db.connect()
db.create_tables([User, Groups])

# create GOD if not exists
try:
    god = User.get(User.tg_id == config.creatorID)
except DoesNotExist:
    god = User.create(tg_id=config.creatorID, username=config.creatorUsername, name='Yury', role=Role.GOD)

# create groups if not exists
_groups = Groups.select()
if len(_groups) == 0:
    for group_no in config.group_numbers:
        Groups.create(group_no=group_no)


@MWT(timeout=5*60)
def get_privilege_ids(role):
    logger.info("Update list of %s", role)
    return [user.tg_id for user in User.select().where(User.role >= role)]


def restricted(role):

    def wrapper(func):
        @wraps(func)
        def wrapped(message, *args, **kwargs):
            user_id = message.chat.id
            if user_id not in get_privilege_ids(role):
                logger.warning("Unauthorized access to <{}> by {}.".format(func.__name__, message.from_user.username))
                return
            return func(message, *args, **kwargs)
        return wrapped

    return wrapper


def check_text(message, func):
    if message.text is None:
        logger.warning("Wrong data format in <{}> by {}".format(func.__name__, message.from_user.username))
        bot.send_message(message.chat.id, config.warningWrongDataFormat)
        bot.register_next_step_handler(message, func)
        return False
    return True


@bot.message_handler(commands=['start'])
def start_cmd(message):
    exists = True
    try:
        user = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        exists = False
    if exists:
        bot.send_message(message.chat.id, config.userRegistered)
        return
    User.create(tg_id=message.chat.id, username=message.from_user.username)
    logger.info('New user registered - @{}'.format(message.from_user.username))
    bot.send_message(message.chat.id, config.greetings)


@bot.message_handler(commands=['set_name'])
def set_name_cmd(message):
    bot.send_message(message.chat.id, config.getName)
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    if message.text is None:
        bot.send_message(message.chat.id, config.wrongName)
        return

    try:
        user = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        logger.warning('@{} has not been registered yet!'.format(message.from_user.username))
        bot.send_message(message.chat.id, config.doesNotExist)
        return
    user.name = message.text
    user.save()
    bot.send_message(message.chat.id, 'Приятно познакомиться, {}'.format(user.name))
    bot.send_message(config.creatorID, 'New user: @{} - {}'.format(user.username, user.name))


@bot.message_handler(commands=['add'])
@restricted(Role.ADMIN)
def add_cmd(message):
    l = message.text.split(' ')
    if len(l) != 3 or not l[1].isdecimal() or not l[2].isdecimal():
        bot.send_message(message.chat.id, 'Wrong format!\n/add group_no points')
        return
    group_no = int(l[1])
    if group_no not in config.group_numbers:
        bot.send_message(message.chat.id, 'Неправильный номер группы!')
        return
    try:
        group = Groups.get(Groups.group_no == group_no)
    except DoesNotExist:
        logger.warning('{} group does not exist!'.format(group_no))
        bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста, попробуйте еще раз.\nЕсли ошибка повторится'
                                          ' - напишите @{}'.format(config.creatorID))
        return
    points = int(l[2])
    if points < 0:
        bot.send_message(message.chat.id, 'Нельзя прибавить отрицательные очки!\nИспользуйте команду /del для '
                                          'снятия очков')
        return
    group.points += points
    group.save()
    logger.info('@{} added {} points to {} group'.format(message.from_user.username, points, group_no))
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(commands=['del'])
@restricted(Role.ADMIN)
def add_cmd(message):
    l = message.text.split(' ')
    if len(l) != 3 or not l[1].isdecimal() or not l[2].isdecimal():
        bot.send_message(message.chat.id, 'Wrong format!\n/del group_no points')
        return
    group_no = int(l[1])
    if group_no not in config.group_numbers:
        bot.send_message(message.chat.id, 'Неправильный номер группы!')
        return
    try:
        group = Groups.get(Groups.group_no == group_no)
    except DoesNotExist:
        logger.warning('{} group does not exist!'.format(group_no))
        bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста, попробуйте еще раз.\nЕсли ошибка повторится'
                                          ' - напишите @{}'.format(config.creatorID))
        return
    points = int(l[2])
    if points < 0:
        bot.send_message(message.chat.id, 'Нельзя отнять отрицательные очки!\nИспользуйте команду /add для '
                                          'добавления очков')
        return
    if group.points < points:
        bot.send_message(message.chat.id, 'У этой группы нет столько очков!')
        return
    group.points -= points
    group.save()
    logger.info('@{} removed {} points from {} group'.format(message.from_user.username, points, group_no))
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(commands=['show'])
def show_cmd(message):
    l = message.text.split(' ')
    if len(l) != 2 or not l[1].isdecimal():
        bot.send_message(message.chat.id, 'Неправильный формат команды!\n/show group_no')
        return
    group_no = int(l[1])
    if group_no not in config.group_numbers:
        bot.send_message(message.chat.id, 'Неправильный номер группы!')
        return
    try:
        group = Groups.get(Groups.group_no == group_no)
    except DoesNotExist:
        logger.warning('{} group does not exist!'.format(group_no))
        bot.send_message(message.chat.id, 'Что-то пошло не так, пожалуйста, попробуйте еще раз.\nЕсли ошибка повторится'
                                          ' - напишите @{}'.format(config.creatorID))
        return
    bot.send_message(message.chat.id, '{} группа - {} очков'.format(group.group_no, group.points))


# TODO: Защита от спама!!!
@MWT(timeout=1 * 60)
def get_rating():
    rating = 'Текущий рейтинг:\n'
    for group in Groups.select().order_by(Groups.points.desc()):
        rating += '{}: {}\n'.format(group.group_no, group.points)
    logger.info('Current rating was updated')
    return rating


@bot.message_handler(commands=['info'])
def info_cmd(message):
    msg = get_rating()
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['make_god'])
@restricted(Role.GOD)
def make_god_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/make_god username')
        return
    username = l[1]
    try:
        user = User.get(User.username == username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    user.role = Role.GOD
    user.save()
    logger.info('User {} - {} become a God'.format(user.name, user.username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(user.tg_id, 'Теперь вы - мой повелитель! Да здравствует, {}!'.format(user.username))


@bot.message_handler(commands=['make_admin'])
@restricted(Role.GOD)
def make_admin_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/make_admin username')
        return
    username = l[1]
    try:
        user = User.get(User.username == username)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'No such user!')
        return
    if user.tg_id == config.creatorID:
        bot.send_message(message.chat.id, "This is my creator! I can't do that")
        return
    user.role = Role.ADMIN
    user.save()
    logger.info('User {} - {} become an admin'.format(user.name, user.username))
    bot.send_message(message.chat.id, 'Success!')
    bot.send_message(user.tg_id, 'You become an Admin!')


@bot.message_handler(commands=['reset'])
@restricted(Role.GOD)
def reset_cmd(message):
    for group in Groups.select():
        group.points = 0
        group.save()
    logger.warning('@{} reset all points'.format(message.from_user.username))
    bot.send_message(message.chat.id, 'All groups was successfully reset!')


@bot.message_handler(commands=['everyone'])
@restricted(Role.ADMIN)
def everyone_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/everyone <message>')
        return
    everyone(l[1])

    bot.send_message(message.chat.id, 'Success!')


def everyone(msg):
    for user in User.select():
        bot.send_message(user.tg_id, msg)


@bot.message_handler(commands=['wall'])
@restricted(Role.ADMIN)
def wall_cmd(message):
    l = message.text.split(' ', maxsplit=1)
    if len(l) < 2:
        bot.send_message(message.chat.id, 'Wrong format!\n/wall <message>')
        return
    message.text = l[1]

    for user in User.select().where(User.role != Role.NONE):
        bot.send_message(user.tg_id, message.text)
    bot.send_message(message.chat.id, 'Success!')


@bot.message_handler(commands=['help'])
def help_cmd(message):
    try:
        user = User.get(User.tg_id == message.chat.id)
    except DoesNotExist:
        bot.send_message(message.chat.id, 'Это бот посвята ВМК МГУ 2019. Зарегистрируйтесь чтобы использовать его.\n'
                                          'Введите команду /start чтобы начать')
        return
    bot.send_message(user.tg_id, config.commands[user.role])


@bot.message_handler(content_types=['sticker'])
def echo_sticker(message):
    bot.send_message(message.chat.id, 'Классный стикер!')


@bot.message_handler(content_types=['text'])
def echo_text(message):
    bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    bot.polling(none_stop=True)
