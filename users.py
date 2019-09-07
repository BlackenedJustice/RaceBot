from peewee import *
from enum import IntEnum
from config import db


class Role(IntEnum):
    NONE = 0
    ADMIN = 1
    GOD = 2


class RoleField(Field):
    field_type = 'smallint'

    def db_value(self, value):
        return int(value)

    def python_value(self, value):
        return Role(value)


class User(Model):
    tg_id = IntegerField(unique=True)
    name = CharField(null=True)
    username = CharField(null=True)
    role = RoleField(default=Role.NONE)

    class Meta:
        database = db


class Groups(Model):
    group_no = IntegerField(unique=True)
    points = IntegerField(default=0)

    class Meta:
        database = db
